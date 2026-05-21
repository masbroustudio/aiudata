from datetime import datetime
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import false, func

from dataline.models.base import DBModel, UUIDMixin
from dataline.utils.encryption import encrypt, decrypt


class LlmConnectionModel(DBModel, UUIDMixin, kw_only=True):
    __tablename__ = "llm_connection"

    provider: Mapped[str] = mapped_column("provider", String, nullable=False)
    model: Mapped[str] = mapped_column("model", String, nullable=False)
    _api_key: Mapped[str | None] = mapped_column("api_key", String, nullable=True)
    base_url: Mapped[str | None] = mapped_column("base_url", String, nullable=True)
    is_default: Mapped[bool] = mapped_column("is_default", Boolean, server_default=false(), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    @property
    def api_key(self) -> str | None:
        return decrypt(self._api_key)

    @api_key.setter
    def api_key(self, value: str | None) -> None:
        self._api_key = encrypt(value)
