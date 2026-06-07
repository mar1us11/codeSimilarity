"""Application configuration.

Settings are loaded from environment variables (prefixed ``CODEGUARD_``) and an
optional ``.env`` file. Everything the analysis pipeline needs to be tuned is
expressed here so that algorithm modules stay free of global state.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_prefix="CODEGUARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Infrastructure -----------------------------------------------------
    database_url: PostgresDsn = Field(
        default=PostgresDsn(
            "postgresql+psycopg://codeguard:codeguard@localhost:5432/codeguard"
        ),
        description="SQLAlchemy database URL (psycopg v3 driver).",
    )
    # NoDecode: keep pydantic-settings from JSON-parsing the env value so a
    # plain comma-separated string is accepted (handled by the validator below).
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    log_level: str = Field(default="INFO")

    # --- Winnowing fingerprinting ------------------------------------------
    winnow_k: int = Field(default=5, ge=1, description="k-gram length for winnowing.")
    winnow_window: int = Field(default=4, ge=1, description="Winnowing window size w.")

    # --- Pipeline fusion ----------------------------------------------------
    weight_ted: float = Field(default=0.50, ge=0.0, le=1.0)
    weight_winnow: float = Field(default=0.35, ge=0.0, le=1.0)
    weight_callgraph: float = Field(default=0.15, ge=0.0, le=1.0)
    match_threshold: float = Field(default=0.60, ge=0.0, le=1.0)

    # --- Cohort analysis ----------------------------------------------------
    #: Minimum fused overall similarity for two submissions to be linked in the
    #: suspicion graph (DFS/BFS clustering of likely-collaborating students).
    cluster_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    #: Run the (independent) pairwise comparisons across processes. Identical
    #: results either way; this only affects wall-clock time. Kill switch:
    #: set CODEGUARD_ANALYSIS_PARALLEL=false to force the sequential path.
    analysis_parallel: bool = Field(default=True)

    # --- AI reference solutions (OpenAI) -----------------------------------
    # The API key is read from the *unprefixed* OPENAI_API_KEY environment
    # variable (the OpenAI SDK's own convention); never hard-code it.
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "CODEGUARD_OPENAI_API_KEY"),
        description="OpenAI API key for generating reference solutions.",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("OPENAI_MODEL", "CODEGUARD_OPENAI_MODEL"),
        description="Chat-completions model used to synthesize reference solutions.",
    )
    #: Default and hard upper bound for how many reference solutions to generate.
    ai_reference_default_count: int = Field(default=5, ge=1, le=50)
    ai_reference_max_count: int = Field(default=15, ge=1, le=50)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        """Allow a comma-separated string in addition to a JSON list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def fusion_weights(self) -> tuple[float, float, float]:
        """The (TED, winnowing, call-graph) weights, renormalized to sum to 1."""
        total = self.weight_ted + self.weight_winnow + self.weight_callgraph
        if total <= 0:
            return (1 / 3, 1 / 3, 1 / 3)
        return (
            self.weight_ted / total,
            self.weight_winnow / total,
            self.weight_callgraph / total,
        )

    @property
    def openai_configured(self) -> bool:
        """True when a *real* OpenAI API key is available.

        The ``.env.example`` placeholder is treated as "not configured" so the
        feature isn't advertised until a real key is supplied.
        """
        key = (self.openai_api_key or "").strip()
        return bool(key) and key != "your_api_key_here"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
