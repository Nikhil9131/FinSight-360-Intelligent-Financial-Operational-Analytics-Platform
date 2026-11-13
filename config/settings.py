"""
FinSight 360 - Application Settings
====================================
Loads configuration from environment variables (.env file).
All database credentials, file paths, and application parameters
are managed here — never hardcoded elsewhere.

Usage:
    from config import get_settings
    settings = get_settings()
    print(settings.DB_HOST)
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv


# ─── Resolve project root (two levels up from config/) ─────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    """
    Immutable application configuration loaded from environment variables.

    Attributes:
        DB_HOST:            PostgreSQL server hostname
        DB_PORT:            PostgreSQL server port
        DB_NAME:            Database name
        DB_USER:            Database username
        DB_PASSWORD:        Database password
        APP_ENV:            Environment (development | staging | production)
        LOG_LEVEL:          Logging level (DEBUG | INFO | WARNING | ERROR)
        DATA_RAW_DIR:       Path to raw data files
        DATA_PROCESSED_DIR: Path to cleaned/processed data
        DATA_SYNTHETIC_DIR: Path to generated synthetic data
        DATA_EXTERNAL_DIR:  Path to external/downloaded data
        LOG_DIR:            Path to log files
        REPORT_OUTPUT_DIR:  Path to Excel report output
        PDF_OUTPUT_DIR:     Path to PDF report output
    """

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "finsight360"
    DB_USER: str = "finsight_user"
    DB_PASSWORD: str = ""

    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Directories (resolved to absolute paths)
    DATA_RAW_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "raw")
    DATA_PROCESSED_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "processed")
    DATA_SYNTHETIC_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "synthetic")
    DATA_EXTERNAL_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "external")
    LOG_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    REPORT_OUTPUT_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "excel" / "reports")
    PDF_OUTPUT_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "excel" / "reports")

    @property
    def DATABASE_URL(self) -> str:
        """SQLAlchemy-compatible connection string."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DSN(self) -> dict:
        """psycopg2-compatible connection parameters."""
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "dbname": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
        }

    def ensure_directories(self) -> None:
        """Create all configured directories if they don't exist."""
        for attr_name in (
            "DATA_RAW_DIR", "DATA_PROCESSED_DIR", "DATA_SYNTHETIC_DIR",
            "DATA_EXTERNAL_DIR", "LOG_DIR", "REPORT_OUTPUT_DIR", "PDF_OUTPUT_DIR",
        ):
            path = getattr(self, attr_name)
            path.mkdir(parents=True, exist_ok=True)


def _resolve_path(env_value: str | None, default: Path) -> Path:
    """Resolve a path from env var string, falling back to default."""
    if env_value:
        p = Path(env_value)
        return p if p.is_absolute() else PROJECT_ROOT / p
    return default


def get_settings(env_file: str | None = None) -> Settings:
    """
    Load settings from the .env file and environment variables.

    Priority: OS environment variable > .env file > default value

    Args:
        env_file: Optional path to a custom .env file.
                  Defaults to PROJECT_ROOT / ".env"

    Returns:
        A populated Settings instance.
    """
    # Load .env file (does NOT override existing OS env vars)
    dotenv_path = Path(env_file) if env_file else PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path)

    defaults = Settings()

    settings = Settings(
        # Database
        DB_HOST=os.getenv("DB_HOST", defaults.DB_HOST),
        DB_PORT=int(os.getenv("DB_PORT", str(defaults.DB_PORT))),
        DB_NAME=os.getenv("DB_NAME", defaults.DB_NAME),
        DB_USER=os.getenv("DB_USER", defaults.DB_USER),
        DB_PASSWORD=os.getenv("DB_PASSWORD", defaults.DB_PASSWORD),

        # Application
        APP_ENV=os.getenv("APP_ENV", defaults.APP_ENV),
        LOG_LEVEL=os.getenv("LOG_LEVEL", defaults.LOG_LEVEL),

        # Directories
        DATA_RAW_DIR=_resolve_path(os.getenv("DATA_RAW_DIR"), defaults.DATA_RAW_DIR),
        DATA_PROCESSED_DIR=_resolve_path(os.getenv("DATA_PROCESSED_DIR"), defaults.DATA_PROCESSED_DIR),
        DATA_SYNTHETIC_DIR=_resolve_path(os.getenv("DATA_SYNTHETIC_DIR"), defaults.DATA_SYNTHETIC_DIR),
        DATA_EXTERNAL_DIR=_resolve_path(os.getenv("DATA_EXTERNAL_DIR"), defaults.DATA_EXTERNAL_DIR),
        LOG_DIR=_resolve_path(os.getenv("LOG_DIR"), defaults.LOG_DIR),
        REPORT_OUTPUT_DIR=_resolve_path(os.getenv("REPORT_OUTPUT_DIR"), defaults.REPORT_OUTPUT_DIR),
        PDF_OUTPUT_DIR=_resolve_path(os.getenv("PDF_OUTPUT_DIR"), defaults.PDF_OUTPUT_DIR),
    )

    # Ensure output directories exist
    settings.ensure_directories()

    return settings
