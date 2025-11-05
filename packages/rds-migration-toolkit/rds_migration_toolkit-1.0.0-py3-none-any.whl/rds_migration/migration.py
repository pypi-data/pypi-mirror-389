"""Main database migration orchestrator."""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from rds_migration.config import MigrationConfig, RDSConfig
from rds_migration.connections import ConnectionManager
from rds_migration.database import Database
from rds_migration.datadog import DataDogMonitor
from rds_migration.logger import get_logger
from rds_migration.materialized_views import MaterializedViewManager
from rds_migration.validation import DatabaseValidator

logger = get_logger(__name__)
console = Console()


@dataclass
class MigrationResult:
    """Result of a database migration."""

    database_name: str
    success: bool
    duration_seconds: float
    error: Optional[str] = None
    rows_migrated: int = 0
    materialized_views_refreshed: int = 0
    size_bytes: int = 0


class DatabaseMigrator:
    """Orchestrates database migrations with materialized view support."""

    def __init__(
        self,
        config: MigrationConfig,
        enable_datadog: bool = True,
        datadog_statsd_host: str = "localhost",
        datadog_statsd_port: int = 8125,
    ) -> None:
        """Initialize database migrator.

        Args:
            config: Migration configuration
            enable_datadog: Whether to enable DataDog monitoring
            datadog_statsd_host: DataDog StatsD host
            datadog_statsd_port: DataDog StatsD port
        """
        self.config = config

        # Initialize DataDog monitoring
        self.monitor = DataDogMonitor(
            enabled=enable_datadog,
            environment=config.environment.value,
            statsd_host=datadog_statsd_host,
            statsd_port=datadog_statsd_port,
        )

        # Initialize source and destination database managers
        self.source_config = RDSConfig(
            rds_id=config.source_rds_id,
            endpoint=self._get_rds_endpoint(config.source_rds_id),
            password=self._get_rds_password(config.source_rds_id),
        )

        self.dest_config = RDSConfig(
            rds_id=config.destination_rds_id,
            endpoint=self._get_rds_endpoint(config.destination_rds_id),
            password=self._get_rds_password(config.destination_rds_id),
        )

        self.source_db = Database(self.source_config, self.monitor)
        self.dest_db = Database(self.dest_config, self.monitor)

        # Initialize connection managers
        self.source_connection_manager = ConnectionManager(self.source_db, self.monitor)
        self.dest_connection_manager = ConnectionManager(self.dest_db, self.monitor)

        # Initialize validators
        self.source_validator = DatabaseValidator(self.source_db, self.monitor)
        self.dest_validator = DatabaseValidator(self.dest_db, self.monitor)

        # Initialize materialized view manager
        self.view_manager = MaterializedViewManager(self.dest_db, self.monitor)

        # Ensure work directory exists
        self.work_dir = Path(config.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Database migrator initialized",
            environment=config.environment.value,
            source=config.source_env,
            destination=config.destination_env,
            work_dir=str(self.work_dir),
        )

    @staticmethod
    def _get_rds_endpoint(rds_id: str) -> str:
        """Get RDS endpoint from AWS.

        Args:
            rds_id: RDS resource ID

        Returns:
            RDS endpoint
        """
        import boto3

        rds = boto3.client("rds")
        response = rds.describe_db_instances()

        for instance in response["DBInstances"]:
            if instance["DbiResourceId"] == rds_id:
                return str(instance["Endpoint"]["Address"])

        raise ValueError(f"RDS instance not found: {rds_id}")

    def _get_rds_password(self, rds_id: str) -> str:
        """Get RDS password from SSM Parameter Store.

        Args:
            rds_id: RDS resource ID

        Returns:
            Password string
        """
        # Build SSM parameter path matching bash script pattern
        # Pattern: /${ENV}/applications/wms/rds/BU_SHARED_PG_PASSWORD
        env = self.config.environment.value
        if env.startswith("fr-"):
            env = env[3:]  # Remove 'fr-' prefix

        ssm_path = f"/{env}/applications/wms/rds/BU_SHARED_PG_PASSWORD"

        logger.info("Retrieving password from SSM", path=ssm_path)

        import boto3

        ssm = boto3.client("ssm")

        try:
            response = ssm.get_parameter(Name=ssm_path, WithDecryption=True)
            logger.info("Password retrieved successfully", path=ssm_path)
            return str(response["Parameter"]["Value"])
        except Exception as e:
            logger.error("Failed to retrieve password from SSM", path=ssm_path, error=str(e))
            raise ValueError(f"Failed to retrieve password from SSM {ssm_path}: {str(e)}") from e

    def get_databases_to_migrate(self) -> list[str]:
        """Get list of databases to migrate.

        Returns:
            List of database names
        """
        # If specific database specified, use only that
        if self.config.specific_database:
            if not self.source_db.database_exists(self.config.specific_database):
                raise ValueError(f"Database not found: {self.config.specific_database}")
            return [self.config.specific_database]

        # Otherwise, get all databases excluding system and excluded ones
        all_databases = self.source_db.list_databases(exclude_system=True)

        # Filter out excluded databases
        databases = [db for db in all_databases if db not in self.config.excluded_databases]

        logger.info(
            "Databases to migrate",
            total=len(databases),
            excluded=len(all_databases) - len(databases),
            databases=databases,
        )

        return databases

    def test_connections(self) -> bool:
        """Test connectivity to source and destination databases.

        Returns:
            True if both connections successful, False otherwise
        """
        logger.info("Testing database connections")

        source_ok = self.source_connection_manager.test_connection()
        dest_ok = self.dest_connection_manager.test_connection()

        if source_ok and dest_ok:
            logger.info("Connection tests passed for both source and destination")
            return True
        elif not source_ok:
            logger.error("Source database connection test failed")
        elif not dest_ok:
            logger.error("Destination database connection test failed")

        return False

    def validate_databases(
        self, databases: Optional[list[str]] = None
    ) -> dict[str, tuple[bool, list[str]]]:
        """Validate databases by comparing source and destination statistics.

        Args:
            databases: List of database names to validate (optional)

        Returns:
            Dictionary mapping database name to (is_valid, list of messages)
        """
        if databases is None:
            databases = self.get_databases_to_migrate()

        logger.info("Validating databases", count=len(databases))

        results = {}

        for database_name in databases:
            logger.info("Validating database", database=database_name)

            # Check if database exists on both sides
            if not self.source_db.database_exists(database_name):
                logger.error("Database not found on source", database=database_name)
                results[database_name] = (False, [f"Database not found on source: {database_name}"])
                continue

            if not self.dest_db.database_exists(database_name):
                logger.error("Database not found on destination", database=database_name)
                results[database_name] = (
                    False,
                    [f"Database not found on destination: {database_name}"],
                )
                continue

            # Get statistics from both sides
            source_stats = self.source_validator.get_database_stats(database_name)
            dest_stats = self.dest_validator.get_database_stats(database_name)

            # Print comparison table
            self.source_validator.print_comparison_table(database_name, source_stats, dest_stats)

            # Validate migration
            is_valid, messages = self.source_validator.validate_migration(
                database_name, source_stats, dest_stats
            )

            results[database_name] = (is_valid, messages)

        return results

    def dump_database(self, database_name: str) -> Path:
        """Dump a database using pg_dump.

        Args:
            database_name: Database name

        Returns:
            Path to dump file
        """
        dump_file = self.work_dir / f"{database_name}.dump"

        logger.info("Dumping database", database=database_name, output=str(dump_file))
        start_time = time.time()

        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h",
            self.source_config.endpoint,
            "-p",
            str(self.source_config.port),
            "-U",
            self.source_config.user,
            "-d",
            database_name,
            "-Fc",  # Custom format
            "-v",  # Verbose
            "-f",
            str(dump_file),
        ]

        # Set password in environment
        env = {"PGPASSWORD": self.source_config.password}

        if self.config.dry_run:
            logger.info("DRY RUN: Would execute pg_dump", command=" ".join(cmd))
            return dump_file

        try:
            if self.monitor:
                with self.monitor.trace_operation(
                    "database.dump", resource=database_name, tags={"database": database_name}
                ):
                    subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
            else:
                subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)

            duration = time.time() - start_time
            size_bytes = dump_file.stat().st_size

            logger.info(
                "Database dumped successfully",
                database=database_name,
                size_mb=size_bytes / 1024 / 1024,
                duration=duration,
            )

            if self.monitor:
                self.monitor.histogram(
                    "database.dump.duration.seconds", duration, tags=[f"database:{database_name}"]
                )
                self.monitor.gauge(
                    "database.dump.size.bytes", size_bytes, tags=[f"database:{database_name}"]
                )

            return dump_file

        except subprocess.CalledProcessError as e:
            logger.error("Database dump failed", database=database_name, error=e.stderr)
            raise

    def restore_database(self, database_name: str, dump_file: Path) -> None:
        """Restore a database using pg_restore.

        Args:
            database_name: Database name
            dump_file: Path to dump file
        """
        logger.info("Restoring database", database=database_name, source=str(dump_file))
        start_time = time.time()

        # Build pg_restore command
        cmd = [
            "pg_restore",
            "-h",
            self.dest_config.endpoint,
            "-p",
            str(self.dest_config.port),
            "-U",
            self.dest_config.user,
            "-d",
            database_name,
            "-v",  # Verbose
            "--no-owner",
            "--no-privileges",
            str(dump_file),
        ]

        # Set password in environment
        env = {"PGPASSWORD": self.dest_config.password}

        if self.config.dry_run:
            logger.info("DRY RUN: Would execute pg_restore", command=" ".join(cmd))
            return

        try:
            if self.monitor:
                with self.monitor.trace_operation(
                    "database.restore", resource=database_name, tags={"database": database_name}
                ):
                    subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
            else:
                subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)

            duration = time.time() - start_time
            logger.info("Database restored successfully", database=database_name, duration=duration)

            if self.monitor:
                self.monitor.histogram(
                    "database.restore.duration.seconds",
                    duration,
                    tags=[f"database:{database_name}"],
                )

        except subprocess.CalledProcessError as e:
            logger.error("Database restore failed", database=database_name, error=e.stderr)
            raise

    def migrate_database(self, database_name: str) -> MigrationResult:
        """Migrate a single database.

        Args:
            database_name: Database name

        Returns:
            MigrationResult object
        """
        logger.info("Starting database migration", database=database_name)
        start_time = time.time()

        if self.monitor:
            self.monitor.record_migration_start(
                database_name, self.config.source_env, self.config.destination_env
            )

        try:
            # Step 1: Dump database
            dump_file = self.dump_database(database_name)

            # Step 2: Restore database
            self.restore_database(database_name, dump_file)

            # Step 3: Refresh materialized views if enabled
            views_refreshed = 0
            if self.config.refresh_materialized_views:
                if self.view_manager.should_refresh_views(database_name):
                    logger.info("Refreshing materialized views", database=database_name)
                    results = self.view_manager.refresh_all_views(database_name)
                    views_refreshed = sum(1 for success, _, _ in results.values() if success)
                    logger.info(
                        "Materialized views refreshed",
                        database=database_name,
                        count=views_refreshed,
                    )

            # Step 4: VACUUM ANALYZE
            logger.info("Running VACUUM ANALYZE", database=database_name)
            self.dest_db.vacuum_analyze(database_name)

            # Get final stats
            size_bytes = self.dest_db.get_database_size(database_name)
            duration = time.time() - start_time

            result = MigrationResult(
                database_name=database_name,
                success=True,
                duration_seconds=duration,
                materialized_views_refreshed=views_refreshed,
                size_bytes=size_bytes,
            )

            logger.info(
                "Database migration completed",
                database=database_name,
                duration=duration,
                views_refreshed=views_refreshed,
            )

            if self.monitor:
                self.monitor.record_migration_success(database_name, duration, 0, views_refreshed)

            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            logger.error("Database migration failed", database=database_name, error=error_msg)

            if self.monitor:
                self.monitor.record_migration_failure(database_name, error_msg, duration)

            return MigrationResult(
                database_name=database_name,
                success=False,
                duration_seconds=duration,
                error=error_msg,
            )

    def migrate_all(self) -> list[MigrationResult]:
        """Migrate all configured databases.

        Returns:
            List of MigrationResult objects
        """
        # Test connections before starting migration
        console.print("\n[bold]Testing database connections...[/bold]")
        if not self.test_connections():
            logger.error("Pre-migration connection test failed")
            console.print("[red]Connection test failed. Cannot proceed with migration.[/red]\n")
            return []
        console.print("[green]✓ Connection tests passed[/green]\n")

        databases = self.get_databases_to_migrate()

        if not databases:
            logger.warning("No databases to migrate")
            return []

        console.print(f"[bold]Migrating {len(databases)} database(s)[/bold]\n")

        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for database in databases:
                task = progress.add_task(f"Migrating {database}...", total=None)

                result = self.migrate_database(database)
                results.append(result)

                if result.success:
                    progress.update(task, description=f"✓ {database} migrated successfully")
                else:
                    progress.update(task, description=f"✗ {database} failed: {result.error}")

        # Print summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        console.print("\n[bold]Migration Summary[/bold]")
        console.print(f"  Total: {len(results)}")
        console.print(f"  [green]Successful: {successful}[/green]")
        console.print(f"  [red]Failed: {failed}[/red]\n")

        return results
