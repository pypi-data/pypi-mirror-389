"""LangGraph instrumentation module for Fiddler."""

from collections.abc import Callable, Collection
from typing import Any, cast

from langchain_core.callbacks import BaseCallbackManager
from langchain_core.language_models import BaseLanguageModel
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableBinding
from langchain_core.tools import BaseTool
from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from pydantic import ConfigDict, validate_call
from wrapt import wrap_function_wrapper

from fiddler_langgraph.core.attributes import (
    _CONVERSATION_ID,
    FIDDLER_METADATA_KEY,
    FiddlerSpanAttributes,
)
from fiddler_langgraph.core.client import FiddlerClient
from fiddler_langgraph.tracing.callback import _CallbackHandler
from fiddler_langgraph.tracing.util import _check_langgraph_version, _get_package_version


@validate_call(config=ConfigDict(strict=True))
def set_conversation_id(conversation_id: str) -> None:
    """Set the conversation ID for the current application invocation.
    This will remain in use until it is called again with a new conversation ID.
    Note (Robin 11th Sep 2025): This should be moved to the core.attributes module in the future.
    """
    _CONVERSATION_ID.set(conversation_id)


@validate_call(config=ConfigDict(strict=True, arbitrary_types_allowed=True))
def _set_default_metadata(
    node: BaseLanguageModel | BaseRetriever | BaseTool,
) -> None:
    """Ensures a node has the default Fiddler metadata dictionary.

    If `node.metadata` does not exist or is not a dictionary, it will be
    initialized. This function modifies the node in place.

    Args:
        node (BaseLanguageModel | BaseRetriever | BaseTool): The node to modify.
    """
    if not hasattr(node, 'metadata'):
        node.metadata = {}
    if not isinstance(node.metadata, dict):
        node.metadata = {}
    metadata = node.metadata
    if FIDDLER_METADATA_KEY not in metadata:
        metadata[FIDDLER_METADATA_KEY] = {}


@validate_call(config=ConfigDict(strict=True, arbitrary_types_allowed=True))
def add_span_attributes(
    node: BaseLanguageModel | BaseRetriever | BaseTool,
    **kwargs: Any,
) -> None:
    """Adds Fiddler-specific attributes to a runnable's metadata.

    This is used for various runnable types like LLM calls, tool
    calls, and retriever calls.

    Args:
        node (BaseLanguageModel | BaseRetriever | BaseTool): The runnable node.
        **kwargs: The attributes to add as key-value pairs.
    """
    _set_default_metadata(node)
    metadata = cast(dict[str, Any], node.metadata)
    fiddler_attrs = cast(dict[str, Any], metadata.get(FIDDLER_METADATA_KEY, {}))
    for key, value in kwargs.items():
        fiddler_attrs[key] = value


@validate_call(config=ConfigDict(strict=True))
def set_llm_context(llm: BaseLanguageModel | RunnableBinding, context: str) -> None:
    """Sets a context string on a language model instance.
    If the language model is a RunnableBinding, the context will be set on the bound object.

    https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.RunnableBinding.html

    The bound object of the RunnableBinding must be a BaseLanguageModel.
    This context can be used to provide additional information about the
    environment or data that the language model is being used in. This
    information will be attached to the spans created for this model.
    In case the user passes a RunnableBinding, the context will be set on the
    bound object.

    Args:
        llm (BaseLanguageModel | RunnableBinding): The language model instance. **Required**.
        context (str): The context string to add. **Required**.

    Examples:
        >>> from langchain_openai import ChatOpenAI
        >>> from fiddler_langgraph.tracing.instrumentation import set_llm_context
        >>>
        >>> llm = ChatOpenAI()
        >>> set_llm_context(llm, "This is a test context.")
        >>>
        >>> # If you are using a RunnableBinding, you can pass the bound object
        >>> # directly to set_llm_context.
        >>> bound_llm = llm.bind(x=1)
        >>> set_llm_context(bound_llm, "This is a test context.")
    """
    if isinstance(llm, RunnableBinding):
        if not isinstance(llm.bound, BaseLanguageModel):
            raise TypeError(
                'llm must be a BaseLanguageModel or a RunnableBinding of a BaseLanguageModel'
            )
        # RunnableBinding has config attribute (which can store metadata), however these are not passed
        # to the callback handlers. So we need to use the bound object directly.
        _llm = llm.bound
    else:
        _llm = llm

    _set_default_metadata(_llm)

    if _llm.metadata is None:
        _llm.metadata = {}
    fiddler_attrs = cast(dict[str, Any], _llm.metadata.get(FIDDLER_METADATA_KEY, {}))
    fiddler_attrs[FiddlerSpanAttributes.LLM_CONTEXT] = context


class LangGraphInstrumentor(BaseInstrumentor):
    """An OpenTelemetry instrumentor for LangGraph applications.

    This class provides automatic instrumentation for applications built with
    LangGraph. It captures traces from the execution of LangGraph graphs and
    sends them to the Fiddler platform.

    To use the instrumentor, you first need to create a `FiddlerClient`
    instance. Then, you can create an instance of `LangGraphInstrumentor` and
    call the `instrument()` method.

    Examples:
        >>> from fiddler_langgraph import FiddlerClient
        >>> from fiddler_langgraph.tracing import LangGraphInstrumentor
        >>>
        >>> client = FiddlerClient(api_key="...", application_id="...")
        >>> instrumentor = LangGraphInstrumentor(client=client)
        >>> instrumentor.instrument()

    Attributes:
        _client (FiddlerClient): The FiddlerClient instance used for configuration.
    """

    def __init__(self, client: FiddlerClient):
        """Initializes the LangGraphInstrumentor.

        Args:
            client (FiddlerClient): The `FiddlerClient` instance. **Required**.

        Raises:
            ImportError: If LangGraph version is incompatible or not installed.
        """
        super().__init__()
        self._client = client
        self._langgraph_version = _get_package_version('langgraph')
        self._langchain_version = _get_package_version('langchain_core')
        self._fiddler_langgraph_version = _get_package_version('fiddler_langgraph')

        self._client.update_resource(
            {
                'lib.langgraph.version': self._langgraph_version.public,
                'lib.langchain_core.version': self._langchain_version.public,
                'lib.fiddler-langgraph.version': self._fiddler_langgraph_version.public,
            }
        )
        self._tracer: _CallbackHandler | None = None
        self._original_callback_manager_init: Callable[..., None] | None = None

        # Check LangGraph version compatibility - we don't add this to dependencies
        # because we leave it to the user to install the correct version of LangGraph
        # We will check if the user installed version is compatible with the version of fiddler-langgraph
        _check_langgraph_version(self._langgraph_version)

    def instrumentation_dependencies(self) -> Collection[str]:
        """Returns the package dependencies required for this instrumentor.

        Returns:
            Collection[str]: A collection of package dependency strings.
        """
        return ('langchain_core >= 0.1.0',)

    def _instrument(self, **kwargs: Any) -> None:
        """Instruments LangGraph by monkey-patching `BaseCallbackManager`.

        This method injects a custom callback handler into LangGraph's callback
        system to capture trace data. This is done by wrapping the `__init__`
        method of `BaseCallbackManager` to inject a `_CallbackHandler`.

        Raises:
            ValueError: If the tracer is not initialized in the FiddlerClient.
        """
        import langchain_core

        tracer = self._client.get_tracer()
        if tracer is None:
            raise ValueError('Context tracer is not initialized')

        self._tracer = _CallbackHandler(tracer)
        self._original_callback_manager_init = langchain_core.callbacks.BaseCallbackManager.__init__
        wrap_function_wrapper(
            module='langchain_core.callbacks',
            name='BaseCallbackManager.__init__',
            wrapper=_BaseCallbackManagerInit(self._tracer),
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        """Removes the instrumentation from LangGraph.

        This is done by restoring the original `__init__` method on the
        `BaseCallbackManager` class.
        """
        import langchain_core

        if self._original_callback_manager_init is not None:
            setattr(  # noqa: B010
                langchain_core.callbacks.BaseCallbackManager,
                '__init__',
                self._original_callback_manager_init,
            )
        self._original_callback_manager_init = None
        self._tracer = None


class _BaseCallbackManagerInit:
    """A wrapper class for `BaseCallbackManager.__init__` to inject Fiddler's callback handler."""

    __slots__ = ('_callback_handler',)

    def __init__(self, callback_handler: _CallbackHandler):
        """Initializes the wrapper.

        Args:
            callback_handler (_CallbackHandler): The Fiddler callback handler instance
                to be injected into the callback manager.
        """
        self._callback_handler = callback_handler

    def __call__(
        self,
        wrapped: Callable[..., None],
        instance: 'BaseCallbackManager',
        args: Any,
        kwargs: Any,
    ) -> None:
        """Calls the original `__init__` and then adds the Fiddler handler.

        It also ensures that the handler is not added multiple times if it
        already exists in the list of inheritable handlers.
        """
        wrapped(*args, **kwargs)
        for handler in instance.inheritable_handlers:
            # Handlers may be copied when new managers are created, so we
            # don't want to keep adding. E.g. see the following location.
            # https://github.com/langchain-ai/langchain/blob/5c2538b9f7fb64afed2a918b621d9d8681c7ae32/libs/core/langchain_core/callbacks/manager.py#L1876
            if isinstance(handler, type(self._callback_handler)):
                break
        else:
            instance.add_handler(self._callback_handler, True)
