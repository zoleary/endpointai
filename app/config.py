"""Configuration loaded from environment / .env file."""
import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


class Settings:
    def __init__(self) -> None:
        self.client_id = _get("CLIENT_ID")
        self.client_secret = _get("CLIENT_SECRET")  # never log or return this
        self.id_host = _get("ID", "https://id.zsai.sqrx.io").rstrip("/")
        self.api_host = _get("API", "https://use2.api.zsai.sqrx.io").rstrip("/")
        self.timeout = float(_get("ZSAI_TIMEOUT", "20") or 20)
        default_mode = "live" if (self.client_id and self.client_secret) else "mock"
        self.mode = (_get("DEMO_MODE") or default_mode).lower()

    @property
    def region(self) -> str:
        # https://use2.api.zsai.sqrx.io -> use2
        host = self.api_host.split("://", 1)[-1]
        return host.split(".", 1)[0] if ".api." in host else host


settings = Settings()
