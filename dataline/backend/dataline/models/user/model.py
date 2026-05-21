from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import true, false

from dataline.models.base import DBModel, UUIDMixin


class UserModel(DBModel, UUIDMixin, kw_only=True):
    __tablename__ = "user"
    name: Mapped[str | None] = mapped_column("name", String(100), nullable=True)
    langsmith_api_key: Mapped[str | None] = mapped_column("langsmith_api_key", String, nullable=True)
    sentry_enabled: Mapped[bool] = mapped_column("sentry_enabled", Boolean, server_default=true())
    analytics_enabled: Mapped[bool] = mapped_column("analytics_enabled", Boolean, server_default=true())
    hide_sql_preference: Mapped[bool] = mapped_column("hide_sql_preference", Boolean, server_default=false())
