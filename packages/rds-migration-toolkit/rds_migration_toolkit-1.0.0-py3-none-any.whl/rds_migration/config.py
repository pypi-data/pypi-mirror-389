"""Configuration management for RDS migrations."""

from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Supported environments."""

    STAGING = "staging"
    PRODUCTION = "production"


class RDSConfig(BaseSettings):
    """RDS configuration from environment variables and AWS SSM."""

    rds_id: str
    endpoint: str
    password: str
    port: int = 5432
    user: str = "superuser"

    class Config:
        env_prefix = ""


class MigrationConfig(BaseSettings):
    """Main migration configuration."""

    # Environment
    environment: Environment

    # Source and destination
    source_env: str
    destination_env: str

    # RDS Connection Details
    source_rds_id: str
    destination_rds_id: str

    # Optional database filter
    specific_database: Optional[str] = None

    # Excluded databases
    excluded_databases: list[str] = Field(
        default_factory=lambda: [
            "culinary_operations_server_primary",
            "simone_primary",
            "wms_bu_shared_postgres_96_fr_staging_encrypted",
            "magic_n_primary",
            "cabinet_primary",
        ]
    )

    # Migration options
    validate_only: bool = False
    refresh_materialized_views: bool = True
    parallel_workers: int = 1
    dry_run: bool = False

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Paths
    work_dir: str = "./sql"
    backup_retention_days: int = 7

    class Config:
        env_prefix = "RDS_MIGRATION_"
        case_sensitive = False

    @classmethod
    def for_environment(
        cls, env: Environment, specific_db: Optional[str] = None
    ) -> "MigrationConfig":
        """Create configuration for a specific environment."""
        if env == Environment.STAGING:
            source_rds_id = "c6ij7o5awpip"
            dest_rds_id = "cvg0uwsamc8a"
        elif env == Environment.PRODUCTION:
            source_rds_id = "c6xyghnmhhdn"
            dest_rds_id = "cpiwaawsumfj"
        else:
            raise ValueError(f"Unsupported environment: {env}")

        return cls(
            environment=env,
            source_env=f"fr-{env.value}",
            destination_env=env.value,
            source_rds_id=source_rds_id,
            destination_rds_id=dest_rds_id,
            specific_database=specific_db,
        )
