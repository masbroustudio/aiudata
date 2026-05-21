from typing import Callable, Literal, ParamSpec, TypeVar

from mirascope.core import litellm
from mirascope.core.base import BaseMessageParam
from pydantic import BaseModel


class OpenAIClientOptions(BaseModel):
    api_key: str | None = None
    base_url: str | None = None


# We now support any string model instead of just a literal
AvailableModels = str

_T = TypeVar("_T", bound=BaseModel)
P = ParamSpec("P")


def call(
    model: AvailableModels,
    response_model: type[_T],
    prompt_fn: Callable[P, list[BaseMessageParam]],
    client_options: OpenAIClientOptions,
) -> Callable[P, _T]:
    import os

    # Map model prefix to provider-specific env var (same logic as nodes.py)
    env_key_map = {
        "groq": "GROQ_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "cerebras": "CEREBRAS_API_KEY",
        "ollama": None,
    }
    provider = model.split("/")[0] if "/" in model else "openai"
    env_var = env_key_map.get(provider, "OPENAI_API_KEY")

    if client_options.api_key and env_var:
        os.environ[env_var] = client_options.api_key
    if client_options.base_url:
        os.environ["LITELLM_API_BASE"] = client_options.base_url

    return litellm.call(
        model=model,
        response_model=response_model,
        json_mode=True,
    )(prompt_fn)
