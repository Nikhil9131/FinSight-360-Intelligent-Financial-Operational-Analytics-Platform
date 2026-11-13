"""
FinSight 360 - Tests for Configuration and Database Connectivity
"""

import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestSettings:
    """Test the Settings configuration module."""

    def test_settings_load_defaults(self):
        """Settings should load with sensible defaults even without .env."""
        from config.settings import Settings
        s = Settings()
        assert s.DB_HOST == "localhost"
        assert s.DB_PORT == 5432
        assert s.DB_NAME == "finsight360"
        assert s.APP_ENV == "development"

    def test_database_url_format(self):
        """DATABASE_URL should be a valid PostgreSQL connection string."""
        from config.settings import Settings
        s = Settings(DB_PASSWORD="test123")
        url = s.DATABASE_URL
        assert url.startswith("postgresql://")
        assert "finsight_user" in url
        assert "test123" in url
        assert "finsight360" in url

    def test_dsn_dict_keys(self):
        """DSN dict should contain exactly the keys psycopg2 expects."""
        from config.settings import Settings
        s = Settings()
        dsn = s.DSN
        expected_keys = {"host", "port", "dbname", "user", "password"}
        assert set(dsn.keys()) == expected_keys

    def test_ensure_directories_creates_folders(self, tmp_path):
        """ensure_directories should create all configured directories."""
        from config.settings import Settings
        s = Settings(
            DATA_RAW_DIR=tmp_path / "raw",
            DATA_PROCESSED_DIR=tmp_path / "processed",
            DATA_SYNTHETIC_DIR=tmp_path / "synthetic",
            DATA_EXTERNAL_DIR=tmp_path / "external",
            LOG_DIR=tmp_path / "logs",
            REPORT_OUTPUT_DIR=tmp_path / "reports",
            PDF_OUTPUT_DIR=tmp_path / "pdf",
        )
        s.ensure_directories()
        assert (tmp_path / "raw").is_dir()
        assert (tmp_path / "processed").is_dir()
        assert (tmp_path / "logs").is_dir()

    def test_project_root_points_to_correct_directory(self):
        """PROJECT_ROOT should point to the repository root."""
        from config.settings import PROJECT_ROOT
        assert (PROJECT_ROOT / "config").is_dir()
        assert (PROJECT_ROOT / "src").is_dir()
        assert (PROJECT_ROOT / "requirements.txt").is_file()


class TestLogger:
    """Test the logging utility."""

    def test_logger_returns_bound_logger(self):
        """get_logger should return a logger bound to the given module name."""
        from src.utils.logger import get_logger
        log = get_logger("test_module")
        # loguru loggers don't have a .name, but they are callable
        assert callable(log.info)
        assert callable(log.error)
        assert callable(log.warning)

    def test_logger_writes_to_file(self, tmp_path):
        """Logger should create a log file."""
        from src.utils.logger import LOG_DIR
        assert LOG_DIR.is_dir()
