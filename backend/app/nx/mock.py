"""Cliente simulado: permite desarrollar la web y el curso sin un servidor Nx."""

from __future__ import annotations

import random
import time
import uuid
from typing import Any

# PNG gris de 1x1 píxel como miniatura de relleno.
_PLACEHOLDER_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c63a8a8a8f80f0004fe02fea7d6a4"
    "e60000000049454e44ae426082"
)

MOCK_DEVICES = [
    {"id": "a1b2c3d4-0000-0000-0000-000000000001", "name": "Entrada principal", "status": "Recording",
     "vendor": "Simulada", "model": "RTSP", "url": "rtsp://simulator:8554/cam1"},
    {"id": "a1b2c3d4-0000-0000-0000-000000000002", "name": "Parking", "status": "Online",
     "vendor": "Simulada", "model": "RTSP", "url": "rtsp://simulator:8554/cam2"},
    {"id": "a1b2c3d4-0000-0000-0000-000000000003", "name": "Pasillo tienda", "status": "Online",
     "vendor": "Simulada", "model": "RTSP", "url": "rtsp://simulator:8554/cam3"},
    {"id": "a1b2c3d4-0000-0000-0000-000000000004", "name": "Muelle de carga", "status": "Offline",
     "vendor": "Simulada", "model": "RTSP", "url": "rtsp://simulator:8554/cam4"},
]

_OBJECT_TYPES = ["nx.base.Person", "nx.base.Vehicle", "nx.base.Bicycle"]


class MockNxClient:
    def __init__(self) -> None:
        self.generic_events: list[dict[str, Any]] = []

    async def access_token(self) -> str:
        return "mock-token"

    async def system_info(self) -> dict[str, Any]:
        return {"name": "Sistema simulado", "version": "6.1.0-mock", "cloudId": "mock-system", "localId": "mock-system"}

    async def list_devices(self) -> list[dict[str, Any]]:
        return list(MOCK_DEVICES)

    async def get_device(self, device_id: str) -> dict[str, Any] | None:
        return next((d for d in MOCK_DEVICES if d["id"] == device_id), None)

    async def device_image(self, device_id: str) -> tuple[bytes, str]:
        return _PLACEHOLDER_PNG, "image/png"

    async def object_tracks(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        rng = random.Random(42)
        now_ms = int(time.time() * 1000)
        device_id = params.get("deviceId")
        devices = [d for d in MOCK_DEVICES if not device_id or d["id"] == device_id]
        limit = int(params.get("limit", 20))
        tracks = []
        for i in range(limit):
            dev = rng.choice(devices) if devices else MOCK_DEVICES[0]
            start = now_ms - rng.randint(0, 3_600_000)
            tracks.append({
                "id": str(uuid.UUID(int=rng.getrandbits(128))),
                "deviceId": dev["id"],
                "objectTypeId": rng.choice(_OBJECT_TYPES),
                "firstAppearanceTimeMs": start,
                "lastAppearanceTimeMs": start + rng.randint(1_000, 30_000),
                "attributes": [{"name": "Confianza", "value": f"{rng.uniform(0.5, 0.99):.2f}"}],
            })
        return sorted(tracks, key=lambda t: t["firstAppearanceTimeMs"], reverse=True)

    async def event_log(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        now_ms = int(time.time() * 1000)
        base = [
            {"eventType": "cameraMotionEvent", "deviceId": MOCK_DEVICES[0]["id"],
             "timestampMs": now_ms - 60_000, "caption": "Movimiento detectado"},
            {"eventType": "analyticsObjectDetected", "deviceId": MOCK_DEVICES[1]["id"],
             "timestampMs": now_ms - 300_000, "caption": "Vehículo en zona restringida"},
            {"eventType": "cameraDisconnectEvent", "deviceId": MOCK_DEVICES[3]["id"],
             "timestampMs": now_ms - 900_000, "caption": "Cámara desconectada"},
        ]
        return self.generic_events[::-1] + base

    async def create_generic_event(
        self, source: str, caption: str, description: str, camera_ids: list[str]
    ) -> None:
        self.generic_events.append({
            "eventType": "userDefinedEvent",
            "deviceId": camera_ids[0] if camera_ids else None,
            "timestampMs": int(time.time() * 1000),
            "caption": caption,
            "description": description,
            "source": source,
        })

    async def close(self) -> None:
        return None
