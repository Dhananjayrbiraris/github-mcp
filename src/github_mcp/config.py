"""Configuration settings for GithubMCP using pydantic-settings."""

import json
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for GithubMCP server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GITHUB_TOKEN: str | None = None
    GITHUB_USERNAME: str | None = None
    ALLOWED_PATHS: list[str] = ["~/projects", "~/workspace", "."]
    MAX_FILE_SIZE_MB: int = 10
    TRANSPORT: str = "stdio"

    @field_validator("ALLOWED_PATHS", mode="before")
    @classmethod
    def parse_allowed_paths(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    parsed = json.loads(v_trimmed)
                    if isinstance(parsed, list):
                        return [str(p) for p in parsed]
                except Exception:
                    pass
            return [p.strip() for p in v_trimmed.split(",") if p.strip()]
        if isinstance(v, list):
            return [str(p) for p in v]
        return ["~/projects", "~/workspace", "."]

    def get_allowed_paths(self) -> list[Path]:
        """Resolve and expand allowed paths."""
        resolved: list[Path] = []
        for path_str in self.ALLOWED_PATHS:
            try:
                p = Path(path_str).expanduser().resolve()
                resolved.append(p)
            except Exception:
                continue
        # Always allow current working directory as safe fallback
        try:
            cwd = Path.cwd().resolve()
            if cwd not in resolved:
                resolved.append(cwd)
        except Exception:
            pass
        return resolved


settings = Settings()
