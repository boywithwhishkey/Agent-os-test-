from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import require_api_key
from app.memory.factory import build_memory_service
from app.memory.models import MemoryContext, MemoryQuery, MemoryRecord, MemoryWrite

router = APIRouter(
    prefix="/api/v1/memory",
    tags=["memory"],
    dependencies=[Depends(require_api_key)],
)
memory_service = build_memory_service()


@router.post("", response_model=MemoryRecord, status_code=status.HTTP_201_CREATED)
async def write_memory(payload: MemoryWrite) -> MemoryRecord:
    return await memory_service.remember(payload)


@router.post("/search", response_model=list[MemoryRecord])
async def search_memory(payload: MemoryQuery) -> list[MemoryRecord]:
    return await memory_service.recall(payload)


@router.post("/context", response_model=MemoryContext)
async def build_memory_context(payload: MemoryQuery) -> MemoryContext:
    return await memory_service.build_context(payload)


@router.get("/{memory_id}", response_model=MemoryRecord)
async def get_memory(memory_id: str) -> MemoryRecord:
    record = await memory_service.store.get(memory_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return record


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: str) -> None:
    deleted = await memory_service.store.delete(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
