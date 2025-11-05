"""
RDS Migration Library

A production-grade database migration tool for AWS RDS PostgreSQL databases
with comprehensive support for materialized views, roles, and extensions.
Includes DataDog monitoring via the 'databaseMigrationLibrary' service.

Architected and Coded by Arthur Mandel arhtur.mandel@external.freshrealm.com.

"""

__version__ = "1.0.0"

from rds_migration.config import MigrationConfig, RDSConfig
from rds_migration.connections import ConnectionManager
from rds_migration.database import Database
from rds_migration.datadog import DataDogMonitor
from rds_migration.migration import DatabaseMigrator, MigrationResult
from rds_migration.validation import DatabaseStats, DatabaseValidator, TableStats

__all__ = [
    "MigrationConfig",
    "RDSConfig",
    "Database",
    "DataDogMonitor",
    "ConnectionManager",
    "DatabaseMigrator",
    "MigrationResult",
    "DatabaseValidator",
    "DatabaseStats",
    "TableStats",
]
