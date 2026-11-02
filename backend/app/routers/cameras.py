from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.config import Settings, get_settings
from app.deps import get_nx, nx_call
from app.nx.client import NxClientProtocol

router = APIRouter(prefix="/api/cameras", tags=["cámaras"])


@router.get("")
async def list_cameras(nx: NxClientProtocol = Depends(get_nx)):
    return await nx_call(nx.list_devices())


@router.get("/{camera_id}")
async def get_camera(camera_id: str, nx: NxClientProtocol = Depends(get_nx)):
    device = await nx_call(nx.get_device(camera_id))
    if device is None:
        raise HTTPException(404, "Cámara no encontrada")
    return device


@router.get("/{camera_id}/thumbnail")
async def camera_thumbnail(camera_id: str, nx: NxClientProtocol = Depends(get_nx)):
    content, media_type = await nx_call(nx.device_image(camera_id))
    return Response(content=content, media_type=media_type)


@router.get("/{camera_id}/stream")
async def stream_config(
    camera_id: str,
    nx: NxClientProtocol = Depends(get_nx),
    settings: Settings = Depends(get_settings),
):
    """Datos que necesita @networkoptix/webrtc-stream-manager en el navegador.

    Ojo: entrega un token de Nx al navegador. En el curso, cada alumno debe tener
    su propio usuario de Nx con permisos limitados (pendiente: token por alumno).
    """
    system_id = settings.nx_system_id
    if not system_id:
        info = await nx_call(nx.system_info())
        system_id = info.get("cloudId") or info.get("localId") or ""
    return {
        "mock": settings.mock_mode,
        "systemId": system_id,
        "cameraId": camera_id,
        "accessToken": await nx_call(nx.access_token()),
        "relayUrl": settings.nx_relay_url,
        "useRelayPrefix": settings.nx_use_relay_prefix,
    }
