import asyncio

from fastapi import APIRouter

from app.shutdown import request_shutdown

router = APIRouter(prefix="/api")


@router.post("/shutdown")
async def shutdown_service() -> dict[str, str]:
    loop = asyncio.get_running_loop()
    loop.call_later(0.25, request_shutdown)
    return {"status": "shutting_down"}