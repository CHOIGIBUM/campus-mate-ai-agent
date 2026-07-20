from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError


class Settings(BaseSettings):
    """Environment-backed runtime configuration.

    Secrets are represented as ``SecretStr`` and are never written to disk by the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = Field(
        default="development", validation_alias=AliasChoices("CAMPUS_MATE_ENV", "APP_ENV")
    )
    timezone: str = Field(
        default="Asia/Seoul", validation_alias=AliasChoices("CAMPUS_MATE_TIMEZONE", "TIMEZONE")
    )
    storage_backend: Literal["notion", "json"] = Field(
        default="json", validation_alias=AliasChoices("CAMPUS_MATE_STORAGE_BACKEND", "STORAGE_BACKEND")
    )
    log_level: str = Field(default="INFO", validation_alias="CAMPUS_MATE_LOG_LEVEL")

    notion_api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("NOTION_API_KEY", "NOTION_API")
    )
    notion_data_source_id: str | None = Field(default=None, validation_alias="NOTION_DATA_SOURCE_ID")
    notion_database_id: str | None = Field(default=None, validation_alias="NOTION_DATABASE_ID")
    notion_dashboard_url: str | None = Field(default=None, validation_alias="NOTION_DASHBOARD_URL")
    notion_version: str = Field(default="2026-03-11", validation_alias="NOTION_VERSION")
    notion_upload_posters: bool = Field(default=True, validation_alias="NOTION_UPLOAD_POSTERS")

    slack_bot_token: SecretStr | None = Field(default=None, validation_alias="SLACK_BOT_TOKEN")
    slack_channel_id: str | None = Field(default=None, validation_alias="SLACK_CHANNEL_ID")

    vision_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("CAMPUS_MATE_VISION_API_KEY", "UPSTAGE_API_KEY"),
    )
    vision_base_url: str = Field(
        default="https://api.upstage.ai/v1", validation_alias="CAMPUS_MATE_VISION_BASE_URL"
    )
    vision_model: str | None = Field(default=None, validation_alias="CAMPUS_MATE_VISION_MODEL")
    enable_ocr: bool = Field(default=True, validation_alias="CAMPUS_MATE_ENABLE_OCR")
    enable_vision: bool = Field(default=True, validation_alias="CAMPUS_MATE_ENABLE_VISION")
    ocr_languages: str = Field(default="kor+eng", validation_alias="CAMPUS_MATE_OCR_LANGUAGES")
    tesseract_cmd: str | None = Field(default=None, validation_alias="CAMPUS_MATE_TESSERACT_CMD")

    source_limit: int = Field(default=8, ge=1, le=50, validation_alias="CAMPUS_MATE_SOURCE_LIMIT")
    request_timeout: float = Field(default=20.0, ge=1, le=120, validation_alias="CAMPUS_MATE_REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, ge=0, le=10, validation_alias="CAMPUS_MATE_MAX_RETRIES")

    data_dir: Path = Field(default=Path("data"), validation_alias="CAMPUS_MATE_DATA_DIR")
    artifacts_dir: Path = Field(default=Path("artifacts"), validation_alias="CAMPUS_MATE_ARTIFACTS_DIR")
    profile_path: Path = Field(
        default=Path("data/user_profile.json"), validation_alias="CAMPUS_MATE_PROFILE_PATH"
    )
    local_store_path: Path = Field(
        default=Path("data/opportunities.json"), validation_alias="CAMPUS_MATE_LOCAL_STORE_PATH"
    )

    @field_validator("notion_data_source_id", "notion_database_id", mode="before")
    @classmethod
    def strip_ids(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip().replace("-", "")
            return value or None
        return value

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.local_store_path.parent.mkdir(parents=True, exist_ok=True)

    def require_notion(self) -> None:
        if not self.notion_api_key:
            raise ConfigurationError("NOTION_API_KEY is required for the Notion backend.")
        if not self.notion_data_source_id and not self.notion_database_id:
            raise ConfigurationError(
                "NOTION_DATA_SOURCE_ID or NOTION_DATABASE_ID is required for the Notion backend."
            )

    def require_slack(self) -> None:
        if not self.slack_bot_token:
            raise ConfigurationError("SLACK_BOT_TOKEN is required to send a Slack briefing.")
        if not self.slack_channel_id:
            raise ConfigurationError("SLACK_CHANNEL_ID is required; use the Slack channel ID, not its name.")
