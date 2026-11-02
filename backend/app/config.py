from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno (o de un archivo .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Servidor Nx. Si NX_URL está vacío, el backend usa datos simulados (modo mock).
    nx_url: str = ""
    nx_username: str = ""
    nx_password: str = ""
    # Nx usa certificados autofirmados por defecto; en producción, poner True.
    nx_verify_tls: bool = False
    # ID del sistema para WebRTC. Si está vacío se toma de /rest/v3/system/info.
    nx_system_id: str = ""
    # Plantilla del relay WebRTC. Nx Cloud: "{systemId}.relay.vmsproxy.com".
    # Servidor local: "nx.midominio.com:7001" con nx_use_relay_prefix=False.
    nx_relay_url: str = "{systemId}.relay.vmsproxy.com"
    nx_use_relay_prefix: bool = True

    # Secreto compartido para los webhooks que envía el motor de reglas de Nx.
    webhook_secret: str = "cambiar-este-secreto"

    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def mock_mode(self) -> bool:
        return not self.nx_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
