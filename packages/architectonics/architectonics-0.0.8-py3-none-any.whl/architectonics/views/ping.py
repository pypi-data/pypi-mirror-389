from fastapi import APIRouter

ping_router = APIRouter()


@ping_router.get(
    "/ping/",
    tags=["system"],
)
async def ping():
    return {"ping": "pong"}
