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

    def update_parameter(self, param_name: str, value: Any) -> bool:
        """Update a single model parameter at runtime.

        Args:
            param_name: Name of the parameter to update
            value: New value for the parameter

        Returns:
            True if successful

        Raises:
            ValueError: If parameter name is invalid or value is out of range

        Example:
            >>> manager.update_parameter("temperature", 0.7)
            >>> manager.update_parameter("top_k", 40)
        """
        # Map of valid parameter names to their types and validation
        valid_params = {
            "temperature": (float, 0.0, 2.0),
            "max_tokens": (int, 1, None),
            "top_p": (float, 0.0, 1.0),
            "num_ctx": (int, 1, None),
            "top_k": (int, 0, None),
            "min_p": (float, 0.0, 1.0),
            "repeat_penalty": (float, 0.0, 2.0),
            "repeat_last_n": (int, -1, None),
            "presence_penalty": (float, -2.0, 2.0),
            "frequency_penalty": (float, -2.0, 2.0),
            "mirostat": (int, 0, 2),
            "mirostat_tau": (float, 0.0, None),
            "mirostat_eta": (float, 0.0, 1.0),
            "seed": (int, -1, None),
        }

        if param_name not in valid_params:
            raise ValueError(
                f"Invalid parameter '{param_name}'. "
                f"Valid parameters: {', '.join(valid_params.keys())}"
            )

        param_type, min_val, max_val = valid_params[param_name]

        # Type conversion
        try:
            if param_type == int:
                value = int(value)
            elif param_type == float:
                value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value type for {param_name}. Expected {param_type.__name__}")

        # Range validation
        if min_val is not None and value < min_val:
            raise ValueError(f"{param_name} must be >= {min_val}")
        if max_val is not None and value > max_val:
            raise ValueError(f"{param_name} must be <= {max_val}")

        # Update the config
        setattr(self.config.config.models.settings, param_name, value)

        # Clear LLM cache to force recreation with new parameters
        self._llm_cache.clear()

        if self.logger:
            self.logger.info(f"Updated parameter {param_name} = {value}")

        return True

    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current model parameters.

        Returns:
            Dictionary of all current parameter values

        Example:
            >>> params = manager.get_current_parameters()
            >>> print(params["temperature"])
        """
        settings = self.config.config.models.settings
        return {
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "top_p": settings.top_p,
            "num_ctx": settings.num_ctx,
            "top_k": settings.top_k,
            "min_p": settings.min_p,
            "repeat_penalty": settings.repeat_penalty,
            "repeat_last_n": settings.repeat_last_n,
            "presence_penalty": settings.presence_penalty,
            "frequency_penalty": settings.frequency_penalty,
            "mirostat": settings.mirostat,
            "mirostat_tau": settings.mirostat_tau,
            "mirostat_eta": settings.mirostat_eta,
            "seed": settings.seed,
        }

    def apply_preset(self, preset_name: str) -> bool:
        """Apply a parameter preset.

        Args:
            preset_name: Name of the preset to apply

        Returns:
            True if successful

        Raises:
            ValueError: If preset name is invalid

        Example:
            >>> manager.apply_preset("creative")
            >>> manager.apply_preset("precise")
        """
        from core.config import PARAMETER_PRESETS

        if preset_name not in PARAMETER_PRESETS:
            available = ", ".join(PARAMETER_PRESETS.keys())
            raise ValueError(
                f"Invalid preset '{preset_name}'. "
                f"Available presets: {available}"
            )

        preset = PARAMETER_PRESETS[preset_name]

        # Apply all settings from the preset
        for param_name, value in preset.settings.items():
            setattr(self.config.config.models.settings, param_name, value)

        # Clear LLM cache
        self._llm_cache.clear()

        if self.logger:
            self.logger.info(f"Applied preset '{preset_name}': {preset.description}")

        return True

    def reset_parameters(self) -> bool:
        """Reset parameters to config file defaults.

        Returns:
            True if successful

        Example:
            >>> manager.reset_parameters()
        """
        # Reload config from file
        self.config.reload()

        # Clear LLM cache
        self._llm_cache.clear()

        if self.logger:
            self.logger.info("Reset parameters to config defaults")

        return True

    # ========== Profile Management ==========

    def list_profiles(self) -> Dict[str, Dict[str, Any]]:
        """List all available parameter profiles.

        Returns:
            Dictionary mapping profile names to profile info (name, description, settings)

        Example:
            >>> profiles = manager.list_profiles()
            >>> for name, info in profiles.items():
            ...     print(f"{name}: {info['description']}")
        """
        profiles = {}

        if self.config.config.parameter_profiles:
            for name, profile in self.config.config.parameter_profiles.items():
                profiles[name] = {
                    'name': profile.name,
                    'description': profile.description,
                    'settings': profile.settings
                }

        return profiles

    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific profile by name.

        Args:
            profile_name: Name of the profile

        Returns:
            Profile info dict or None if not found

        Example:
            >>> profile = manager.get_profile("creative_coding")
            >>> print(profile['description'])
        """
        if not self.config.config.parameter_profiles:
            return None

        profile = self.config.config.parameter_profiles.get(profile_name)
        if not profile:
            return None

        return {
            'name': profile.name,
            'description': profile.description,
            'settings': profile.settings
        }

    def apply_profile(self, profile_name: str) -> bool:
        """Apply a parameter profile.

        Args:
            profile_name: Name of the profile to apply

        Returns:
            True if successful, False if profile not found

        Example:
            >>> manager.apply_profile("creative_coding")
        """
        from core.config import ParameterProfile

        # Check if profile exists
        if not self.config.config.parameter_profiles:
            if self.logger:
                self.logger.error(f"No profiles defined in config")
            return False

        profile = self.config.config.parameter_profiles.get(profile_name)
        if not profile:
            if self.logger:
                self.logger.error(f"Profile not found: {profile_name}")
            return False

        # Apply each setting in the profile
        for param_name, value in profile.settings.items():
            if not self.update_parameter(param_name, value):
                if self.logger:
                    self.logger.error(f"Failed to apply parameter {param_name} from profile {profile_name}")
                return False

        # Clear LLM cache
        self._llm_cache.clear()

        if self.logger:
            self.logger.info(f"Applied profile: {profile_name}")

        return True

    def create_profile(self, name: str, description: str, settings: Dict[str, Any]) -> bool:
        """Create a new parameter profile.

        Args:
            name: Profile name
            description: Profile description
            settings: Dictionary of parameter settings

        Returns:
            True if successful, False on error

        Example:
            >>> manager.create_profile(
            ...     "my_profile",
            ...     "Custom profile for my use case",
            ...     {"temperature": 0.5, "top_p": 0.9}
            ... )
        """
        from core.config import ParameterProfile

        try:
            # Create profile object (validates settings)
            profile = ParameterProfile(
                name=name,
                description=description,
                settings=settings
            )

            # Initialize parameter_profiles if it doesn't exist
            if self.config.config.parameter_profiles is None:
                self.config.config.parameter_profiles = {}

            # Add to config
            self.config.config.parameter_profiles[name] = profile

            # Save to file
            self.config.save()

            if self.logger:
                self.logger.info(f"Created profile: {name}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create profile {name}: {e}")
            return False

    def delete_profile(self, profile_name: str) -> bool:
        """Delete a parameter profile.

        Args:
            profile_name: Name of the profile to delete

        Returns:
            True if successful, False if profile not found

        Example:
            >>> manager.delete_profile("my_profile")
        """
        if not self.config.config.parameter_profiles:
            if self.logger:
                self.logger.error("No profiles defined in config")
            return False

        if profile_name not in self.config.config.parameter_profiles:
            if self.logger:
                self.logger.error(f"Profile not found: {profile_name}")
            return False

        # Remove from config
        del self.config.config.parameter_profiles[profile_name]

        # Save to file
        self.config.save()

        if self.logger:
            self.logger.info(f"Deleted profile: {profile_name}")

        return True

    def export_profile(self, profile_name: str, output_path: Optional[str] = None) -> bool:
        """Export a profile to JSON file.

        Args:
            profile_name: Name of the profile to export
            output_path: Output file path (default: ./{profile_name}_profile.json)

        Returns:
            True if successful, False on error

        Example:
            >>> manager.export_profile("creative_coding", "./my_profile.json")
        """
        import json
        from pathlib import Path

        # Get profile
        profile = self.get_profile(profile_name)
        if not profile:
            if self.logger:
                self.logger.error(f"Profile not found: {profile_name}")
            return False

        # Default output path
        if output_path is None:
            output_path = f"./{profile_name}_profile.json"

        try:
            # Write to file
            output_file = Path(output_path)
            with open(output_file, 'w') as f:
                json.dump(profile, f, indent=2)

            if self.logger:
                self.logger.info(f"Exported profile {profile_name} to {output_path}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to export profile: {e}")
            return False

    def import_profile(self, input_path: str) -> bool:
        """Import a profile from JSON file.

        Args:
            input_path: Path to JSON file

        Returns:
            True if successful, False on error

        Example:
            >>> manager.import_profile("./my_profile.json")
        """
        import json
        from pathlib import Path

        try:
            # Read file
            input_file = Path(input_path)
            if not input_file.exists():
                if self.logger:
                    self.logger.error(f"File not found: {input_path}")
                return False

            with open(input_file, 'r') as f:
                profile_data = json.load(f)

            # Validate required fields
            if 'name' not in profile_data or 'description' not in profile_data or 'settings' not in profile_data:
                if self.logger:
                    self.logger.error("Invalid profile format: missing required fields")
                return False

            # Create profile
            return self.create_profile(
                name=profile_data['name'],
                description=profile_data['description'],
                settings=profile_data['settings']
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to import profile: {e}")
            return False
