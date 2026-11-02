from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.deps import get_nx, nx_call
from app.nx.client import NxClientProtocol

router = APIRouter(prefix="/api", tags=["analíticas"])


@router.get("/analytics/objects")
async def object_tracks(
    device_id: str | None = Query(None, alias="deviceId"),
    limit: int = Query(20, ge=1, le=500),
    nx: NxClientProtocol = Depends(get_nx),
):
    params: dict = {"limit": limit}
    if device_id:
        params["deviceId"] = device_id
    return await nx_call(nx.object_tracks(params))


@router.get("/events")
async def event_log(
    device_id: str | None = Query(None, alias="deviceId"),
    nx: NxClientProtocol = Depends(get_nx),
):
    params = {"deviceId": device_id} if device_id else {}
    return await nx_call(nx.event_log(params))


class GenericEventIn(BaseModel):
    source: str = Field("softmind-ai", max_length=100)
    caption: str = Field(..., max_length=200)
    description: str = Field("", max_length=2000)
    camera_ids: list[str] = Field(default_factory=list, alias="cameraIds")


@router.post("/events/generic", status_code=202)
async def create_generic_event(body: GenericEventIn, nx: NxClientProtocol = Depends(get_nx)):
    """Usado por el worker de IA: crea un Generic Event en Nx para disparar reglas."""
    await nx_call(nx.create_generic_event(body.source, body.caption, body.description, body.camera_ids))
    return {"status": "enviado"}
