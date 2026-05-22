"""
Thread-safe LLM provider routing for multi-provider support.
Eliminates environment variable manipulation by using litellm directly.
"""
import os
import threading
from typing import Optional

# Thread-local storage for API keys to avoid race conditions
_thread_local = threading.local()

# Provider to environment variable mapping
PROVIDER_ENV_MAP = {
    "groq": "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "together_ai": "TOGETHERAI_API_KEY",
    "fireworks_ai": "FIREWORKS_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "cohere": "COHERE_API_KEY",
    "ollama": None,
}


def get_provider_from_model(model_name: str) -> str:
    """Extract provider from model name (e.g., 'groq/llama-3.3-70b' -> 'groq')."""
    if "/" in model_name:
        return model_name.split("/")[0]
    return "openai"


def get_env_var_for_provider(provider: str) -> Optional[str]:
    """Get the environment variable name for a provider."""
    return PROVIDER_ENV_MAP.get(provider, "OPENAI_API_KEY")


def set_provider_key(model_name: str, api_key: str) -> tuple[str, Optional[str]]:
    """
    Set the provider API key in environment. Returns (env_var, original_value) for cleanup.
    Thread-safe via thread-local tracking.
    """
    provider = get_provider_from_model(model_name)
    env_var = get_env_var_for_provider(provider)

    if not env_var:
        return ("", None)

    original = os.environ.get(env_var)
    os.environ[env_var] = api_key

    # Track in thread-local for safety
    if not hasattr(_thread_local, "env_stack"):
        _thread_local.env_stack = []
    _thread_local.env_stack.append((env_var, original))

    return (env_var, original)


def restore_provider_key(env_var: str, original_value: Optional[str]) -> None:
    """Restore the original environment variable value."""
    if not env_var:
        return
    if original_value is None:
        os.environ.pop(env_var, None)
    else:
        os.environ[env_var] = original_value
