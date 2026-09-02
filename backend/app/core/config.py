from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://agrivision:agrivision@localhost:3306/agrivision"

    cors_origins: str = "http://localhost:5173"

    segmentation_backend: str = "classical_cv"  # "classical_cv" | "unet"
    # Relative by default so it resolves correctly both in Docker (WORKDIR /app)
    # and in a local dev run (cwd = backend/) without needing an env override —
    # only override MODEL_CHECKPOINT_PATH/STORAGE_ROOT for a non-standard layout.
    model_checkpoint_path: str = "models_store/classifier_best.pt"

    storage_root: str = "storage"

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def uploads_dir(self) -> Path:
        path = Path(self.storage_root) / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def reports_dir(self) -> Path:
        path = Path(self.storage_root) / "reports"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
