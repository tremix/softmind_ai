"""Cliente de la REST API de Nx Witness / Nx Meta.

Los endpoints cambian entre versiones (v3/v4). Se basan en la documentación
pública de Gen 6 y aún no se han probado contra un servidor real: verifícalos
en la API integrada del servidor que instales y ajusta aquí si hace falta.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

import httpx


class NxError(Exception):
    pass


class NxClientProtocol(Protocol):
    async def system_info(self) -> dict[str, Any]: ...
    async def list_devices(self) -> list[dict[str, Any]]: ...
    async def get_device(self, device_id: str) -> dict[str, Any] | None: ...
    async def device_image(self, device_id: str) -> tuple[bytes, str]: ...
    async def object_tracks(self, params: dict[str, Any]) -> list[dict[str, Any]]: ...
    async def event_log(self, params: dict[str, Any]) -> list[dict[str, Any]]: ...
    async def create_generic_event(
        self, source: str, caption: str, description: str, camera_ids: list[str]
    ) -> None: ...
    async def access_token(self) -> str: ...
    async def close(self) -> None: ...


def normalize_device(raw: dict[str, Any]) -> dict[str, Any]:
    """Reduce el objeto de dispositivo de Nx a los campos que usa la web."""
    return {
        "id": str(raw.get("id", "")).strip("{}"),
        "name": raw.get("name", "Sin nombre"),
        "status": raw.get("status", "Unknown"),
        "vendor": raw.get("vendor", ""),
        "model": raw.get("model", ""),
        "url": raw.get("url", ""),
    }


class NxClient:
    """Cliente real. Inicia sesión con usuario/contraseña y reutiliza el token Bearer."""

    def __init__(self, base_url: str, username: str, password: str, verify_tls: bool):
        self._username = username
        self._password = password
        self._token: str | None = None
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"), verify=verify_tls, timeout=15.0
        )

    async def _login(self) -> str:
        resp = await self._http.post(
            "/rest/v3/login/sessions",
            json={"username": self._username, "password": self._password},
        )
        if resp.status_code != 200:
            raise NxError(f"Login en Nx falló ({resp.status_code}): {resp.text[:200]}")
        self._token = resp.json()["token"]
        return self._token

    async def access_token(self) -> str:
        return self._token or await self._login()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        token = await self.access_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self._http.request(method, path, headers=headers, **kwargs)
        if resp.status_code == 401:  # token caducado: reintentar una vez
            token = await self._login()
            headers["Authorization"] = f"Bearer {token}"
            resp = await self._http.request(method, path, headers=headers, **kwargs)
        if resp.status_code >= 400:
            raise NxError(f"{method} {path} → {resp.status_code}: {resp.text[:200]}")
        return resp

    async def system_info(self) -> dict[str, Any]:
        return (await self._request("GET", "/rest/v3/system/info")).json()

    async def list_devices(self) -> list[dict[str, Any]]:
        data = (await self._request("GET", "/rest/v3/devices")).json()
        return [normalize_device(d) for d in data]

    async def get_device(self, device_id: str) -> dict[str, Any] | None:
        try:
            data = (await self._request("GET", f"/rest/v3/devices/{device_id}")).json()
        except NxError:
            return None
        return normalize_device(data)

    async def device_image(self, device_id: str) -> tuple[bytes, str]:
        resp = await self._request("GET", f"/rest/v3/devices/{device_id}/image")
        return resp.content, resp.headers.get("content-type", "image/jpeg")

    async def object_tracks(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        # Nx 6.1+. En versiones anteriores: /ec2/analyticsLookupObjectTracks
        return (await self._request("GET", "/rest/v4/analytics/objectTracks", params=params)).json()

    async def event_log(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        return (await self._request("GET", "/rest/v4/events/log", params=params)).json()

    async def create_generic_event(
        self, source: str, caption: str, description: str, camera_ids: list[str]
    ) -> None:
        params = {
            "source": source,
            "caption": caption,
            "description": description,
            "metadata": json.dumps({"cameraRefs": camera_ids}),
        }
        await self._request("GET", "/api/createEvent", params=params)

    async def close(self) -> None:
        await self._http.aclose()
