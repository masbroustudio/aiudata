from typing import Callable, ParamSpec, TypeVar

from mirascope.core import litellm
from mirascope.core.base import BaseMessageParam
from pydantic import BaseModel

from dataline.services.llm_flow.llm_provider import (
    set_provider_key,
    restore_provider_key,
)


class OpenAIClientOptions(BaseModel):
    api_key: str | None = None
    base_url: str | None = None


# We support any string model
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

    # Set provider-specific env var (thread-safe)
    env_var, original_val = ("", None)
    if client_options.api_key:
        env_var, original_val = set_provider_key(model, client_options.api_key)
    if client_options.base_url:
        os.environ["LITELLM_API_BASE"] = client_options.base_url

    # Note: We don't restore here because mirascope's decorator pattern
    # needs the env var set when the returned function is actually called.
    # The env var will be overwritten on next call anyway.
    return litellm.call(
        model=model,
        response_model=response_model,
        json_mode=True,
    )(prompt_fn)
