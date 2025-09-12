"""Main configuration for VQE Exam Topic Prediction System."""

from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field

from .logging import app_logger


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = Field(default="VQE Exam Topic Prediction System", env="APP_NAME")
    version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")

    # Quantum computing settings
    max_qubits: int = Field(default=6, env="MAX_QUBITS")
    max_iterations: int = Field(default=100, env="MAX_ITERATIONS")
    quantum_available: bool = Field(default=True, env="QUANTUM_AVAILABLE")

    # Data settings
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    logs_dir: Path = Field(default=Path("logs"), env="LOGS_DIR")

    # Model settings
    confidence_level: float = Field(default=0.95, env="CONFIDENCE_LEVEL")
    min_historical_years: int = Field(default=3, env="MIN_HISTORICAL_YEARS")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(exist_ok=True)
settings.logs_dir.mkdir(exist_ok=True)

# Initialize logging
app_logger.info("Configuration loaded", settings=settings.dict())


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
