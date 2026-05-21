from typing import Type
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from dataline.models.llm_connection.model import LlmConnectionModel
from dataline.models.llm_connection.schema import LlmConnectionCreate, LlmConnectionUpdate
from dataline.repositories.base import BaseRepository, NotFoundError


class LlmConnectionRepository(BaseRepository[LlmConnectionModel, LlmConnectionCreate, LlmConnectionUpdate]):
    def __init__(self) -> None:
        super().__init__()

    @property
    def model(self) -> Type[LlmConnectionModel]:
        return LlmConnectionModel

    async def get_default(self, session: AsyncSession) -> LlmConnectionModel | None:
        stmt = select(LlmConnectionModel).where(LlmConnectionModel.is_default == True)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def set_default(self, session: AsyncSession, connection_id: str) -> LlmConnectionModel:
        # Unset all
        stmt_unset = update(LlmConnectionModel).values(is_default=False)
        await session.execute(stmt_unset)
        
        # Set new default
        stmt_set = (
            update(LlmConnectionModel)
            .where(LlmConnectionModel.id == connection_id)
            .values(is_default=True)
            .returning(LlmConnectionModel)
        )
        result = await session.execute(stmt_set)
        updated = result.scalars().first()
        if not updated:
            raise NotFoundError("Connection not found")
            
        await session.flush()
        return updated

    async def create(self, session: AsyncSession, data: LlmConnectionCreate) -> LlmConnectionModel:
        if data.is_default:
            stmt_unset = update(LlmConnectionModel).values(is_default=False)
            await session.execute(stmt_unset)

        new_record = LlmConnectionModel(
            id=str(uuid.uuid4()),
            provider=data.provider,
            model=data.model,
            api_key=data.api_key,
            base_url=data.base_url,
            is_default=data.is_default,
        )
        session.add(new_record)
        await session.flush()
        return new_record

    async def update_by_uuid(
        self, session: AsyncSession, record_id: str, data: LlmConnectionUpdate
    ) -> LlmConnectionModel:
        if data.is_default:
            stmt_unset = update(LlmConnectionModel).values(is_default=False)
            await session.execute(stmt_unset)

        update_data = data.model_dump(exclude_unset=True)
        record = await self.get_by_uuid(session, record_id)
        if not record:
            raise NotFoundError("Connection not found")

        for key, value in update_data.items():
            setattr(record, key, value)
            
        await session.flush()
        await session.refresh(record)
        return record
