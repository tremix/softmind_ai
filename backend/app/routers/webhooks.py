"""Recibe las peticiones HTTP que envía el motor de reglas de Nx (acción "HTTP request").

Configura en Nx una regla con URL:
  https://<backend>/api/webhooks/nx?secret=<WEBHOOK_SECRET>
"""

import hmac
import time
from collections import deque
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import Settings, get_settings

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

# Memoria temporal. Pendiente: guardar en PostgreSQL.
RECENT: deque[dict[str, Any]] = deque(maxlen=200)


@router.post("/nx", status_code=204)
async def nx_webhook(
    request: Request,
    secret: str = Query(...),
    settings: Settings = Depends(get_settings),
):
    if not hmac.compare_digest(secret, settings.webhook_secret):
        raise HTTPException(403, "Secreto inválido")
    raw = await request.body()
    try:
        payload: Any = await request.json()
    except ValueError:
        payload = raw.decode(errors="replace")[:5000]
    RECENT.append({"receivedAtMs": int(time.time() * 1000), "payload": payload})


@router.get("/nx")
async def recent_webhooks():
    return list(RECENT)[::-1]
