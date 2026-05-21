import logging
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_serializer

logger = logging.getLogger(__name__)


class UserUpdateIn(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=250)
    langsmith_api_key: Optional[SecretStr] = Field(None, min_length=4)
    sentry_enabled: Optional[bool] = None
    analytics_enabled: Optional[bool] = None
    hide_sql_preference: Optional[bool] = None

    @field_serializer("langsmith_api_key")
    def dump_langsmith_api_key(self, v: SecretStr | None) -> str | None:
        return v.get_secret_value() if v else None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    langsmith_api_key: Optional[SecretStr] = None
    sentry_enabled: bool
    analytics_enabled: Optional[bool] = None
    hide_sql_preference: Optional[bool] = None


class UserWithKeys(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None

    langsmith_api_key: SecretStr | None = None
    sentry_enabled: bool
    analytics_enabled: Optional[bool] = None
    hide_sql_preference: Optional[bool] = None


class AvatarOut(BaseModel):
    blob: str
