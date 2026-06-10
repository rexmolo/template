from fastapi import APIRouter

from app.api.v1.health import HealthData
from app.core.responses import Envelope, ok

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/health", response_model=Envelope[HealthData])
async def public_health() -> Envelope[HealthData]:
    return ok(HealthData(status="ok"))
