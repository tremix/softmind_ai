from fastapi import HTTPException, Request

from app.nx.client import NxClientProtocol, NxError


def get_nx(request: Request) -> NxClientProtocol:
    return request.app.state.nx


async def nx_call(coro):
    """Convierte errores de Nx en 502 para que el frontend los muestre claramente."""
    try:
        return await coro
    except NxError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
