import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LLM_API_KEYS: str = "key1,key2"
    LLM_MODEL: str = "openai/gpt-4o-mini"
    LLM_PROVIDER: str = "openai"
    LLM_API_BASE: Optional[str] = None
    DATABASE_URL: str = "sqlite:////data/app.db"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,*"
    ENABLE_FAILURE_SIMULATION: bool = True
    LITELLM_CACHE_ENABLED: bool = True
    CACHE_DIR: str = "/data/cache"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def key_pool(self) -> List[str]:
        raw_keys = [k.strip() for k in self.LLM_API_KEYS.split(",") if k.strip()]
        return raw_keys

    @property
    def key_dict(self) -> dict:
        """Returns dict mapping key_1, key_2, ... to the actual secret key."""
        return {f"key_{i+1}": key for i, key in enumerate(self.key_pool)}

    @property
    def resolved_database_url(self) -> str:
        """
        If /data/app.db is requested but /data cannot be written to (e.g. running outside docker),
        fall back gracefully to a local path while keeping sqlite.
        """
        url = self.DATABASE_URL
        if url.startswith("sqlite:////data/"):
            data_dir = Path("/data")
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
                test_file = data_dir / ".write_test"
                test_file.touch()
                test_file.unlink()
                return url
            except (PermissionError, OSError):
                local_dir = Path("./data")
                local_dir.mkdir(parents=True, exist_ok=True)
                relative_path = url[len("sqlite:////data/"):]
                return f"sqlite:///{local_dir.resolve()}/{relative_path}"
        elif url.startswith("sqlite:///"):
            path_str = url[len("sqlite:///"):]
            path = Path(path_str)
            if not path.is_absolute():
                path = Path.cwd() / path
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{path.resolve()}"
        return url

    @property
    def resolved_cache_dir(self) -> str:
        cache_path = Path(self.CACHE_DIR)
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
            test_file = cache_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return str(cache_path.resolve())
        except (PermissionError, OSError):
            local_cache = Path("./data/cache")
            local_cache.mkdir(parents=True, exist_ok=True)
            return str(local_cache.resolve())


settings = Settings()
