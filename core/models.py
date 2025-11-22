"""Ollama model manager for Meton.

This module provides comprehensive model management for interacting with
local Ollama instances, including generation, chat, streaming, and model switching.

Example:
    >>> from core.config import Config
    >>> from core.models import ModelManager
    >>>
    >>> config = Config()
    >>> manager = ModelManager(config)
    >>>
    >>> # Simple generation
    >>> response = manager.generate("Write a hello world function")
    >>>
    >>> # Streaming generation
    >>> for chunk in manager.generate("Explain Python", stream=True):
    >>>     print(chunk, end='', flush=True)
    >>>
    >>> # Chat with history
    >>> messages = [{"role": "user", "content": "Hello!"}]
    >>> response = manager.chat(messages)
"""

import ollama
import sys
from typing import Dict, Any, Optional, List, Union, Iterator
from langchain_ollama import OllamaLLM
from core.config import ConfigLoader


# Custom Exceptions
class ModelError(Exception):
    """Base exception for model-related errors."""
    pass


class ModelNotFoundError(ModelError):
    """Model not available in Ollama."""
    pass


class OllamaConnectionError(ModelError):
    """Cannot connect to Ollama."""
    pass


class ModelManager:
    """Manages Ollama models and provides generation capabilities.

    This class handles all interactions with Ollama, including:
    - Model verification and listing
    - Text generation (streaming and non-streaming)
    - Chat completion with message history
    - Model switching without restart
    - Configuration integration

    Attributes:
        config: Configuration loader instance
        current_model: Currently active model name
        logger: Optional logger instance for operation tracking
    """

    def __init__(self, config: ConfigLoader, logger=None):
        """Initialize model manager.

        Args:
            config: Configuration loader instance
            logger: Optional logger for operation tracking

        Raises:
            OllamaConnectionError: If cannot connect to Ollama

        Example:
            >>> config = Config()
            >>> manager = ModelManager(config)
        """
        self.config = config
        self.current_model = config.get('models.primary')
        self.logger = logger
        self._llm_cache: Dict[str, Ollama] = {}

        # Verify Ollama is accessible
        self._verify_ollama()

        if self.logger:
            self.logger.info(f"ModelManager initialized with {self.current_model}")

    def _verify_ollama(self) -> None:
        """Verify Ollama is running and accessible.

        Raises:
            OllamaConnectionError: If Ollama is not accessible
        """
        try:
            ollama.list()
        except Exception as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama. Is it running?\n"
                f"Start with: ollama serve\n"
                f"Error: {e}"
            )

    def list_available_models(self) -> List[str]:
        """List all available Ollama models.

        Returns:
            List of model names currently available in Ollama

        Example:
            >>> models = manager.list_available_models()
            >>> for model in models:
            >>>     print(model)
        """
        try:
            response = ollama.list()
            models = []

            # Handle ListResponse object (has .models attribute)
            if hasattr(response, 'models'):
                for model in response.models:
                    # Model object has .model attribute with the name
                    if hasattr(model, 'model'):
                        models.append(model.model)
                    elif isinstance(model, str):
                        models.append(model)

            # Fallback for dict response (older versions)
            elif isinstance(response, dict):
                models_list = response.get('models', [])
                for model in models_list:
                    if isinstance(model, dict):
                        name = model.get('name') or model.get('model')
                        if name:
                            models.append(name)
                    elif isinstance(model, str):
                        models.append(model)

            return models
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not list models: {e}")
            return []

    def check_model_available(self, model_name: str) -> bool:
        """Check if a model is available in Ollama.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model exists, False otherwise

        Example:
            >>> if manager.check_model_available("codellama:34b"):
            >>>     print("Model is available!")
        """
        available = self.list_available_models()
        return any(model_name in m for m in available)

    def get_current_model(self) -> str:
        """Get currently active model name.

        Returns:
            Name of the current model

        Example:
            >>> current = manager.get_current_model()
            >>> print(f"Using: {current}")
        """
        return self.current_model

    def resolve_alias(self, alias: str) -> str:
        """Resolve a model alias to full name.

        Supports aliases like "primary", "fallback", "quick", "34b", "13b", "7b".

        Args:
            alias: Model alias or full name

        Returns:
            Full model name

        Example:
            >>> full_name = manager.resolve_alias("primary")
            >>> # Returns "codellama:34b"
        """
        aliases = {
            "34b": self.config.get('models.primary'),
            "13b": self.config.get('models.fallback'),
            "7b": self.config.get('models.quick'),
            "primary": self.config.get('models.primary'),
            "fallback": self.config.get('models.fallback'),
            "quick": self.config.get('models.quick'),
        }
        return aliases.get(alias, alias)

    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model.

        Args:
            model_name: Name or alias of model to switch to

        Returns:
            True if successful

        Raises:
            ModelNotFoundError: If model is not available

        Example:
            >>> manager.switch_model("fallback")  # Switch to 13b
            >>> manager.switch_model("codellama:7b")  # Switch by full name
        """
        # Resolve alias
        full_name = self.resolve_alias(model_name)

        # Verify model exists
        if not self.check_model_available(full_name):
            raise ModelNotFoundError(
                f"Model '{full_name}' not found.\n"
                f"Pull it with: ollama pull {full_name}"
            )

        old_model = self.current_model
        self.current_model = full_name

        if self.logger:
            self.logger.info(f"Switched model: {old_model} → {full_name}")

        return True

    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a model.

        Args:
            model_name: Name of model (defaults to current)

        Returns:
            Model information dictionary with details like size, format, etc.

        Example:
            >>> info = manager.get_model_info()
            >>> print(f"Model size: {info.get('size')}")
        """
        if model_name is None:
            model_name = self.current_model

        try:
            response = ollama.show(model_name)
            return response
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}

    def _get_model_options(self, override_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get model generation options from config with optional overrides.

        Args:
            override_options: Optional dict to override config values

        Returns:
            Dictionary of model options
        """
        settings = self.config.config.models.settings
        options = {
            # Core parameters
            'temperature': settings.temperature,
            'num_predict': settings.max_tokens,
            'top_p': settings.top_p,
            'num_ctx': settings.num_ctx,

            # Advanced sampling
            'top_k': settings.top_k,
            'min_p': settings.min_p,

            # Repetition control
            'repeat_penalty': settings.repeat_penalty,
            'repeat_last_n': settings.repeat_last_n,
            'presence_penalty': settings.presence_penalty,
            'frequency_penalty': settings.frequency_penalty,

            # Mirostat
            'mirostat': settings.mirostat,
            'mirostat_tau': settings.mirostat_tau,
            'mirostat_eta': settings.mirostat_eta,

            # Reproducibility
            'seed': settings.seed,
        }

        if override_options:
            options.update(override_options)

        return options

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, Iterator[str]]:
        """Generate text from a prompt.

        Args:
            prompt: Input prompt for generation
            model: Model name or alias (uses current if None)
            stream: Whether to stream response chunks
            options: Optional dict to override generation parameters

        Returns:
            Generated text (complete string if stream=False, iterator if stream=True)

        Raises:
            ModelNotFoundError: If specified model is not available
            ModelError: If generation fails

        Example:
            >>> # Non-streaming
            >>> response = manager.generate("Write a function")
            >>> print(response)
            >>>
            >>> # Streaming
            >>> for chunk in manager.generate("Explain", stream=True):
            >>>     print(chunk, end='', flush=True)
        """
        # Resolve model name
        if model is None:
            model_name = self.current_model
        else:
            model_name = self.resolve_alias(model)

        # Verify model exists
        if not self.check_model_available(model_name):
            raise ModelNotFoundError(
                f"Model '{model_name}' not found.\n"
                f"Pull it with: ollama pull {model_name}"
            )

        # Get generation options
        gen_options = self._get_model_options(options)

        if self.logger:
            self.logger.debug(f"Generating with {model_name}, stream={stream}")

        try:
            if stream:
                # Streaming generation
                return self._generate_stream(prompt, model_name, gen_options)
            else:
                # Non-streaming generation
                response = ollama.generate(
                    model=model_name,
                    prompt=prompt,
                    options=gen_options
                )

                if isinstance(response, dict):
                    return response.get('response', '')
                return str(response)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Generation failed: {e}")
            raise ModelError(f"Generation failed: {e}")

    def _generate_stream(
        self,
        prompt: str,
        model_name: str,
        options: Dict[str, Any]
    ) -> Iterator[str]:
        """Internal method for streaming generation.

        Args:
            prompt: Input prompt
            model_name: Model to use
            options: Generation options

        Yields:
            Response chunks as they arrive
        """
        try:
            stream = ollama.generate(
                model=model_name,
                prompt=prompt,
                options=options,
                stream=True
            )

            for chunk in stream:
                if isinstance(chunk, dict):
                    text = chunk.get('response', '')
                    if text:
                        yield text
                else:
                    yield str(chunk)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Streaming generation failed: {e}")
            raise ModelError(f"Streaming generation failed: {e}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, Iterator[str]]:
        """Chat completion with message history.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     Roles: 'system', 'user', 'assistant'
            model: Model name or alias (uses current if None)
            stream: Whether to stream response chunks
            options: Optional dict to override generation parameters

        Returns:
            Assistant's response (complete string if stream=False, iterator if stream=True)

        Raises:
            ModelNotFoundError: If specified model is not available
            ModelError: If chat fails

        Example:
            >>> messages = [
            >>>     {"role": "system", "content": "You are a helpful assistant"},
            >>>     {"role": "user", "content": "Hello!"}
            >>> ]
            >>> response = manager.chat(messages)
            >>> print(response)
        """
        # Resolve model name
        if model is None:
            model_name = self.current_model
        else:
            model_name = self.resolve_alias(model)

        # Verify model exists
        if not self.check_model_available(model_name):
            raise ModelNotFoundError(
                f"Model '{model_name}' not found.\n"
                f"Pull it with: ollama pull {model_name}"
            )

        # Get generation options
        gen_options = self._get_model_options(options)

        if self.logger:
            self.logger.debug(f"Chat with {model_name}, {len(messages)} messages, stream={stream}")

        try:
            if stream:
                # Streaming chat
                return self._chat_stream(messages, model_name, gen_options)
            else:
                # Non-streaming chat
                response = ollama.chat(
                    model=model_name,
                    messages=messages,
                    options=gen_options
                )

                if isinstance(response, dict):
                    message = response.get('message', {})
                    return message.get('content', '')
                return str(response)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Chat failed: {e}")
            raise ModelError(f"Chat failed: {e}")

    def _chat_stream(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        options: Dict[str, Any]
    ) -> Iterator[str]:
        """Internal method for streaming chat.

        Args:
            messages: Message history
            model_name: Model to use
            options: Generation options

        Yields:
            Response chunks as they arrive
        """
        try:
            stream = ollama.chat(
                model=model_name,
                messages=messages,
                options=options,
                stream=True
            )

            for chunk in stream:
                if isinstance(chunk, dict):
                    message = chunk.get('message', {})
                    text = message.get('content', '')
                    if text:
                        yield text
                else:
                    yield str(chunk)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Streaming chat failed: {e}")
            raise ModelError(f"Streaming chat failed: {e}")

    def get_llm(self, model_name: Optional[str] = None) -> OllamaLLM:
        """Get or create LangChain OllamaLLM instance (for LangGraph compatibility).

        Args:
            model_name: Name of model to use (defaults to current)

        Returns:
            LangChain OllamaLLM instance

        Example:
            >>> llm = manager.get_llm()
            >>> result = llm.invoke("Hello")
        """
        if model_name is None:
            model_name = self.current_model

        # Return cached instance if available
        if model_name in self._llm_cache:
            return self._llm_cache[model_name]

        # Verify model exists
        if not self.check_model_available(model_name):
            raise ModelNotFoundError(
                f"Model '{model_name}' not found.\n"
                f"Pull it with: ollama pull {model_name}"
            )

        # Create new LLM instance
        settings = self.config.config.models.settings
        llm = OllamaLLM(
            model=model_name,
            # Core parameters
            temperature=settings.temperature,
            num_predict=settings.max_tokens,
            top_p=settings.top_p,
            num_ctx=settings.num_ctx,
            # Advanced sampling
            top_k=settings.top_k,
            min_p=settings.min_p,
            # Repetition control
            repeat_penalty=settings.repeat_penalty,
            repeat_last_n=settings.repeat_last_n,
            presence_penalty=settings.presence_penalty,
            frequency_penalty=settings.frequency_penalty,
            # Mirostat
            mirostat=settings.mirostat,
            mirostat_tau=settings.mirostat_tau,
            mirostat_eta=settings.mirostat_eta,
            # Reproducibility
            seed=settings.seed,
        )

        # Cache and return
        self._llm_cache[model_name] = llm
        return llm
