import os
from typing import Dict, Any, Optional

from langchain_community.chat_models.openai import ChatOpenAI as ChatOpenAIBase
from pydantic import BaseModel, Field, model_validator
from langchain.utils import get_from_dict_or_env
from langchain_community.utils.openai import is_openai_v1

from .client import CrucibleOpenAI
from .async_client import CrucibleAsyncOpenAI

# Handle both old and new LangChain import paths
try:
    from langchain_core.runnables import RunnableLambda, Runnable
except ImportError:
    try:
        from langchain.schema.runnable import RunnableLambda, Runnable
    except ImportError:
        # Fallback: RunnableLambda might not be needed if bind_metadata isn't used
        RunnableLambda = None
        try:
            from langchain_core.runnables.base import Runnable
        except ImportError:
            Runnable = object  # Fallback to object if Runnable not available


class ChatOpenAI(ChatOpenAIBase):
    """
    LangChain ChatOpenAI wrapper for Crucible.
    
    Provides seamless integration with LangChain while automatically
    logging requests and responses to Crucible warehouse.
    """
    
    crucible_kwargs: Dict[str, Any] = Field(
        default_factory=lambda: {"verify_ssl": False}
    )

    def __init__(self, **kwargs):
        """Initialize the ChatOpenAI with Crucible client."""
        # Extract Crucible configuration before calling super()
        crucible_kwargs = kwargs.pop('crucible_kwargs', {})
        
        # Call parent constructor
        super().__init__(**kwargs)
        
        # Create Crucible client if configuration provided
        self._crucible_client = None
        if crucible_kwargs:
            crucible_api_key = crucible_kwargs.get('api_key') or os.getenv('CRUCIBLE_API_KEY')
            crucible_domain = crucible_kwargs.get('domain') or os.getenv('CRUCIBLE_DOMAIN', 'warehouse.usecrucible.ai')
            
            if crucible_api_key:
                # Create Crucible client
                self._crucible_client = CrucibleOpenAI(
                    api_key=crucible_api_key,
                    domain=crucible_domain
                )
                
                # Replace the client with Crucible's wrapped client
                self.client = self._crucible_client.chat.completions
                
                # Store metadata for injection
                self._crucible_metadata = {}

    def bind_metadata(self, **kwargs):
        """Bind metadata to the LLM for use in chains."""
        # Store metadata for use in chains
        if not hasattr(self, "_crucible_metadata"):
            self._crucible_metadata = {}
        
        self._crucible_metadata.update(kwargs)
        
        # Return a wrapper that injects metadata
        def metadata_injector(input_data):
            return self.invoke(input_data, crucible_metadata=self._crucible_metadata)
        
        if RunnableLambda is not None:
            return RunnableLambda(metadata_injector)
        else:
            # Fallback: return a simple callable if RunnableLambda is not available
            return metadata_injector

    def with_metadata(self, **kwargs) -> "ChatOpenAI":
        """
        Add metadata to be sent with Crucible requests.
        
        Args:
            **kwargs: Metadata key-value pairs
            
        Returns:
            ChatOpenAI instance with metadata
        """
        # Store metadata for use in invoke/ainvoke methods
        if not hasattr(self, "_crucible_metadata"):
            self._crucible_metadata = {}
        
        self._crucible_metadata.update(kwargs)
        
        return self

    def with_structured_output(self, schema, **kwargs):
        """
        Return a Runnable that uses structured output.
        
        This method uses OpenAI's function calling API to get structured output,
        ensuring Crucible integration is maintained.
        
        Args:
            schema: The schema to use for structured output (Pydantic model or dict)
            **kwargs: Additional arguments (include_raw, etc.)
            
        Returns:
            A Runnable with structured output support
        """
        # Convert schema to OpenAI tool format
        try:
            from langchain_core.utils.function_calling import convert_to_openai_tool
        except ImportError:
            # Fallback: create tool format manually
            def convert_to_openai_tool(pydantic_model):
                """Convert Pydantic model to OpenAI tool format."""
                schema_dict = pydantic_model.model_json_schema()
                return {
                    "type": "function",
                    "function": {
                        "name": schema_dict.get("title", "extract_data"),
                        "description": schema_dict.get("description", ""),
                        "parameters": schema_dict
                    }
                }
        
        # Convert schema to OpenAI tool format
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            tool = convert_to_openai_tool(schema)
        else:
            tool = schema
        
        # Store reference to self for metadata injection
        original_self = self
        
        def extract_structured_output(response):
            """Extract structured output from the response."""
            # Handle AIMessage with tool calls (LangChain format)
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_call = response.tool_calls[0]
                if isinstance(tool_call, dict):
                    args = tool_call.get('args', {})
                else:
                    # Extract args from ToolCall object
                    args = getattr(tool_call, 'args', {})
                    if not args and hasattr(tool_call, 'get'):
                        args = tool_call.get('args', {})
                    # Try to parse from string if needed
                    if not args and hasattr(tool_call, 'args_str'):
                        import json
                        try:
                            args = json.loads(getattr(tool_call, 'args_str', '{}'))
                        except:
                            pass
                
                if isinstance(schema, type) and issubclass(schema, BaseModel):
                    try:
                        return schema(**args)
                    except Exception as e:
                        # If schema validation fails, try to extract from raw response
                        pass
                return args
            
            # Handle content that might be JSON
            if hasattr(response, 'content') and response.content:
                import json
                try:
                    data = json.loads(response.content)
                    if isinstance(schema, type) and issubclass(schema, BaseModel):
                        return schema(**data)
                    return data
                except:
                    pass
            
            # If no tool calls, return the response as-is
            return response
        
        # Create a wrapper Runnable that processes the output
        def structured_invoke(input_data, config=None, **invoke_kwargs):
            # Inject Crucible metadata if present
            if hasattr(original_self, "_crucible_metadata"):
                invoke_kwargs.setdefault("crucible_metadata", {})
                invoke_kwargs["crucible_metadata"].update(original_self._crucible_metadata)
            
            # Prepare messages for OpenAI API
            if isinstance(input_data, list):
                messages = input_data
            elif hasattr(input_data, 'messages'):
                messages = input_data.messages
            elif hasattr(input_data, 'to_messages'):
                messages = input_data.to_messages()
            else:
                # Convert to message format
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=str(input_data))]
            
            # Extract tool name safely
            if isinstance(tool, dict) and "function" in tool:
                tool_name = tool["function"].get("name", "extract_data")
            else:
                tool_name = "extract_data"
            
            # Call the LLM with tools
            response = original_self.invoke(
                messages,
                config=config,
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": tool_name}},
                **invoke_kwargs
            )
            
            # Extract structured output
            return extract_structured_output(response)
        
        async def structured_ainvoke(input_data, config=None, **invoke_kwargs):
            # Inject Crucible metadata if present
            if hasattr(original_self, "_crucible_metadata"):
                invoke_kwargs.setdefault("crucible_metadata", {})
                invoke_kwargs["crucible_metadata"].update(original_self._crucible_metadata)
            
            # Prepare messages for OpenAI API
            if isinstance(input_data, list):
                messages = input_data
            elif hasattr(input_data, 'messages'):
                messages = input_data.messages
            elif hasattr(input_data, 'to_messages'):
                messages = input_data.to_messages()
            else:
                # Convert to message format
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=str(input_data))]
            
            # Extract tool name safely
            if isinstance(tool, dict) and "function" in tool:
                tool_name = tool["function"].get("name", "extract_data")
            else:
                tool_name = "extract_data"
            
            # Call the LLM with tools
            response = await original_self.ainvoke(
                messages,
                config=config,
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": tool_name}},
                **invoke_kwargs
            )
            
            # Extract structured output
            return extract_structured_output(response)
        
        # Return a Runnable wrapper that inherits from Runnable
        # This ensures compatibility with LangChain's pipe operator (|)
        class StructuredOutputRunnable(Runnable):
            def invoke(self, input_data, config=None, **kwargs):
                return structured_invoke(input_data, config, **kwargs)
            
            async def ainvoke(self, input_data, config=None, **kwargs):
                return await structured_ainvoke(input_data, config, **kwargs)
        
        return StructuredOutputRunnable()

    def invoke(self, input, config=None, **kwargs):
        """
        Invoke the model with input and optional metadata.
        
        Args:
            input: Input to the model
            config: Optional configuration
            **kwargs: Additional arguments
            
        Returns:
            Model response
        """
        # Extract metadata if provided
        crucible_metadata = kwargs.pop("crucible_metadata", {})
        
        # Merge with stored metadata
        if hasattr(self, "_crucible_metadata"):
            crucible_metadata.update(self._crucible_metadata)
        
        # Store metadata for _generate method
        if crucible_metadata:
            self._current_metadata = crucible_metadata
        
        # Remove any Crucible-specific kwargs that shouldn't be passed to OpenAI
        kwargs.pop("_crucible_client", None)
        
        return super().invoke(input, config=config, **kwargs)

    async def ainvoke(self, input, config=None, **kwargs):
        """
        Async invoke the model with input and optional metadata.
        
        Args:
            input: Input to the model
            config: Optional configuration
            **kwargs: Additional arguments
            
        Returns:
            Model response
        """
        # Extract metadata if provided
        crucible_metadata = kwargs.pop("crucible_metadata", {})
        
        # Merge with stored metadata
        if hasattr(self, "_crucible_metadata"):
            crucible_metadata.update(self._crucible_metadata)
        
        # Store metadata for _generate method
        if crucible_metadata:
            self._current_metadata = crucible_metadata
        
        # Remove any Crucible-specific kwargs that shouldn't be passed to OpenAI
        kwargs.pop("_crucible_client", None)
        
        return await super().ainvoke(input, config=config, **kwargs)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Override _generate to inject Crucible metadata."""
        # Get current metadata from invoke method
        crucible_metadata = getattr(self, "_current_metadata", {})
        
        # Add metadata to kwargs if present
        if crucible_metadata:
            kwargs["crucible_metadata"] = crucible_metadata
        
        # Clear current metadata after use
        if hasattr(self, "_current_metadata"):
            delattr(self, "_current_metadata")
        
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def close(self) -> None:
        """Close the Crucible client and flush logs."""
        if hasattr(self, "_crucible_client"):
            self._crucible_client.close()

    def flush_logs(self) -> None:
        """Force flush of pending logs."""
        if hasattr(self, "_crucible_client"):
            self._crucible_client.flush_logs()

    def get_logging_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        if hasattr(self, "_crucible_client"):
            return self._crucible_client.get_logging_stats()
        return {}

    def is_healthy(self) -> bool:
        """Check if client is healthy."""
        if hasattr(self, "_crucible_client"):
            return self._crucible_client.is_healthy()
        return True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass
