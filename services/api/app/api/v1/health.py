from fastapi import APIRouter
from pydantic import BaseModel

from app.core.responses import Envelope, ok

router = APIRouter(prefix="/health", tags=["health"])


class HealthData(BaseModel):
    status: str


@router.get("", response_model=Envelope[HealthData])
async def health() -> Envelope[HealthData]:
    return ok(HealthData(status="ok"))
