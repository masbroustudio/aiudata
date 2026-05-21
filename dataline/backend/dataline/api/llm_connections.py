from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dataline.repositories.base import get_session
from dataline.models.llm_connection.schema import LlmConnectionCreate, LlmConnectionOut, LlmConnectionUpdate
from dataline.repositories.base import NotFoundError
from dataline.repositories.llm_connection import LlmConnectionRepository

router = APIRouter()

def get_repo():
    return LlmConnectionRepository()

@router.get("/", response_model=List[LlmConnectionOut])
async def list_connections(
    session: AsyncSession = Depends(get_session),
    repo: LlmConnectionRepository = Depends(get_repo),
):
    connections = await repo.list_all(session)
    return [LlmConnectionOut.model_validate(c) for c in connections]

@router.post("/", response_model=LlmConnectionOut, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: LlmConnectionCreate,
    session: AsyncSession = Depends(get_session),
    repo: LlmConnectionRepository = Depends(get_repo),
):
    connection = await repo.create(session, data)
    return LlmConnectionOut.model_validate(connection)

@router.put("/{connection_id}", response_model=LlmConnectionOut)
async def update_connection(
    connection_id: str,
    data: LlmConnectionUpdate,
    session: AsyncSession = Depends(get_session),
    repo: LlmConnectionRepository = Depends(get_repo),
):
    try:
        connection = await repo.update_by_uuid(session, connection_id, data)
        return LlmConnectionOut.model_validate(connection)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: str,
    session: AsyncSession = Depends(get_session),
    repo: LlmConnectionRepository = Depends(get_repo),
):
    try:
        await repo.delete_by_uuid(session, connection_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")

@router.post("/{connection_id}/default", response_model=LlmConnectionOut)
async def set_default_connection(
    connection_id: str,
    session: AsyncSession = Depends(get_session),
    repo: LlmConnectionRepository = Depends(get_repo),
):
    try:
        connection = await repo.set_default(session, connection_id)
        return LlmConnectionOut.model_validate(connection)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")
