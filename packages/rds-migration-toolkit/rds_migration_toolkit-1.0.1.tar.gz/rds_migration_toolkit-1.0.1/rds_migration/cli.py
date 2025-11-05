"""Command-line interface for RDS migration tool."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from rds_migration.config import Environment, MigrationConfig
from rds_migration.logger import configure_logging, get_logger
from rds_migration.migration import DatabaseMigrator

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="rds-migrate")
def cli() -> None:
    """RDS Migration Tool with DataDog monitoring.

    A production-grade database migration tool for AWS RDS PostgreSQL databases
    with comprehensive support for materialized views, roles, and extensions.

    Metrics are sent to DataDog under the service name 'databaseMigrationLibrary'.
    """
    pass


@cli.command()
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["staging", "production"], case_sensitive=False),
    required=True,
    help="Target environment (staging or production)",
)
@click.option(
    "--database",
    "-d",
    help="Specific database to migrate (optional, migrates all if not specified)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without actually doing it",
)
@click.option(
    "--no-refresh-views",
    is_flag=True,
    help="Skip refreshing materialized views after migration",
)
@click.option(
    "--work-dir",
    type=click.Path(path_type=Path),
    default="./sql",
    help="Working directory for SQL dumps (default: ./sql)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level (default: INFO)",
)
@click.option(
    "--datadog-host",
    default="localhost",
    help="DataDog StatsD host (default: localhost)",
)
@click.option(
    "--datadog-port",
    type=int,
    default=8125,
    help="DataDog StatsD port (default: 8125)",
)
@click.option(
    "--no-datadog",
    is_flag=True,
    help="Disable DataDog monitoring",
)
def migrate(
    environment: str,
    database: Optional[str],
    dry_run: bool,
    no_refresh_views: bool,
    work_dir: Path,
    log_level: str,
    datadog_host: str,
    datadog_port: int,
    no_datadog: bool,
) -> None:
    """Migrate databases from one RDS instance to another.

    Examples:

        # Migrate all staging databases
        rds-migrate migrate --environment staging

        # Migrate specific database in production
        rds-migrate migrate --environment production --database mydb

        # Dry run to see what would be migrated
        rds-migrate migrate --environment staging --dry-run

        # Migrate without refreshing materialized views
        rds-migrate migrate --environment staging --no-refresh-views

        # Migrate with debug logging and custom DataDog host
        rds-migrate migrate -e staging --log-level DEBUG --datadog-host dd-agent.internal
    """
    # Configure logging
    configure_logging(log_level=log_level)
    logger = get_logger(__name__)

    # Create configuration
    env = Environment(environment.lower())
    config = MigrationConfig.for_environment(env, specific_db=database)

    # Override config options
    config.dry_run = dry_run
    config.refresh_materialized_views = not no_refresh_views
    config.work_dir = str(work_dir)
    config.log_level = log_level

    # Print configuration
    console.print("\n[bold]RDS Migration Configuration[/bold]")
    console.print(f"  Environment: {config.environment.value}")
    console.print(f"  Source: {config.source_env} (RDS ID: {config.source_rds_id})")
    console.print(f"  Destination: {config.destination_env} (RDS ID: {config.destination_rds_id})")
    console.print(f"  Specific Database: {config.specific_database or 'All (except excluded)'}")
    console.print(f"  Refresh Materialized Views: {config.refresh_materialized_views}")
    console.print(f"  Work Directory: {config.work_dir}")
    console.print(f"  Dry Run: {config.dry_run}")
    console.print(f"  DataDog Monitoring: {not no_datadog}")
    if not no_datadog:
        console.print(f"  DataDog Host: {datadog_host}:{datadog_port}")
        console.print("  DataDog Service: databaseMigrationLibrary")
    console.print()

    if dry_run:
        console.print("[yellow]DRY RUN MODE: No actual changes will be made[/yellow]\n")

    # Confirm before proceeding in production
    if env == Environment.PRODUCTION and not dry_run:
        console.print("[bold red]⚠️  PRODUCTION MIGRATION[/bold red]")
        console.print("This will migrate databases in the production environment.\n")
        if not click.confirm("Are you sure you want to continue?"):
            console.print("Migration cancelled.")
            sys.exit(0)

    try:
        # Initialize migrator
        migrator = DatabaseMigrator(
            config,
            enable_datadog=not no_datadog,
            datadog_statsd_host=datadog_host,
            datadog_statsd_port=datadog_port,
        )

        # Run migration
        results = migrator.migrate_all()

        # Print detailed results
        _print_results_table(results)

        # Exit with error code if any migrations failed
        if any(not r.success for r in results):
            sys.exit(1)

    except Exception as e:
        logger.error("Migration failed", error=str(e))
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        sys.exit(1)


@cli.command()
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["staging", "production"], case_sensitive=False),
    required=True,
    help="Target environment",
)
@click.option(
    "--database",
    "-d",
    required=True,
    help="Database name to check",
)
@click.option(
    "--datadog-host",
    default="localhost",
    help="DataDog StatsD host (default: localhost)",
)
@click.option(
    "--datadog-port",
    type=int,
    default=8125,
    help="DataDog StatsD port (default: 8125)",
)
@click.option(
    "--no-datadog",
    is_flag=True,
    help="Disable DataDog monitoring",
)
def list_views(
    environment: str, database: str, datadog_host: str, datadog_port: int, no_datadog: bool
) -> None:
    """List materialized views in a database.

    Example:

        rds-migrate list-views --environment staging --database fulfillment_engine
    """
    from rds_migration.datadog import DataDogMonitor
    from rds_migration.materialized_views import MaterializedViewManager

    configure_logging()
    logger = get_logger(__name__)

    env = Environment(environment.lower())
    config = MigrationConfig.for_environment(env)

    try:
        # Initialize components
        monitor = None
        if not no_datadog:
            monitor = DataDogMonitor(
                enabled=True,
                environment=env.value,
                statsd_host=datadog_host,
                statsd_port=datadog_port,
            )

        # Get destination RDS config
        from rds_migration.migration import DatabaseMigrator

        migrator = DatabaseMigrator(config, enable_datadog=not no_datadog)
        view_manager = MaterializedViewManager(migrator.dest_db, monitor)

        # List views
        views = view_manager.list_materialized_views(database)

        if not views:
            console.print(f"\n[yellow]No materialized views found in {database}[/yellow]\n")
            return

        # Print views table
        table = Table(title=f"Materialized Views in {database}")
        table.add_column("Schema", style="cyan")
        table.add_column("View Name", style="green")
        table.add_column("Has Indexes", style="yellow")
        table.add_column("Row Count", style="blue")

        for view in views:
            row_count = view_manager.get_view_row_count(database, view.name)
            table.add_row(
                view.schema, view.name, "Yes" if view.has_indexes else "No", f"{row_count:,}"
            )

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        logger.error("Failed to list views", error=str(e))
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        sys.exit(1)


@cli.command()
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["staging", "production"], case_sensitive=False),
    required=True,
    help="Target environment",
)
@click.option(
    "--database",
    "-d",
    required=True,
    help="Database name",
)
@click.option(
    "--view",
    "-v",
    help="Specific view to refresh (optional, refreshes all if not specified)",
)
@click.option(
    "--concurrent",
    is_flag=True,
    help="Use REFRESH MATERIALIZED VIEW CONCURRENTLY",
)
def refresh_views(environment: str, database: str, view: Optional[str], concurrent: bool) -> None:
    """Refresh materialized views in a database.

    Examples:

        # Refresh all views in a database
        rds-migrate refresh-views --environment staging --database fulfillment_engine

        # Refresh specific view
        rds-migrate refresh-views -e staging -d fulfillment_engine -v tnm_delivery_options

        # Refresh concurrently (requires unique index)
        rds-migrate refresh-views -e staging -d fulfillment_engine --concurrent
    """
    from rds_migration.materialized_views import MaterializedViewManager

    configure_logging()
    logger = get_logger(__name__)

    env = Environment(environment.lower())
    config = MigrationConfig.for_environment(env)

    try:
        # Initialize components
        from rds_migration.migration import DatabaseMigrator

        migrator = DatabaseMigrator(config)
        view_manager = MaterializedViewManager(migrator.dest_db, migrator.monitor)

        if view:
            # Refresh specific view
            console.print(f"\n[bold]Refreshing view {view} in {database}[/bold]\n")
            success, row_count, duration = view_manager.refresh_materialized_view(
                database, view, concurrent
            )

            if success:
                console.print(
                    f"[green]✓[/green] View refreshed successfully: {row_count:,} rows in {duration:.2f}s\n"
                )
            else:
                console.print("[red]✗[/red] View refresh failed\n")
                sys.exit(1)
        else:
            # Refresh all views
            console.print(f"\n[bold]Refreshing all views in {database}[/bold]\n")
            results = view_manager.refresh_all_views(database, concurrent)

            # Print results table
            table = Table(title="Refresh Results")
            table.add_column("View Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Row Count", style="blue")
            table.add_column("Duration", style="yellow")

            for view_name, (success, row_count, duration) in results.items():
                status = "✓ Success" if success else "✗ Failed"
                status_style = "green" if success else "red"
                table.add_row(
                    view_name,
                    f"[{status_style}]{status}[/{status_style}]",
                    f"{row_count:,}",
                    f"{duration:.2f}s",
                )

            console.print()
            console.print(table)
            console.print()

            # Exit with error if any failed
            if any(not success for success, _, _ in results.values()):
                sys.exit(1)

    except Exception as e:
        logger.error("Failed to refresh views", error=str(e))
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        sys.exit(1)


@cli.command()
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["staging", "production"], case_sensitive=False),
    required=True,
    help="Target environment",
)
@click.option(
    "--database",
    "-d",
    help="Specific database to validate (optional, validates all if not specified)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level (default: INFO)",
)
@click.option(
    "--datadog-host",
    default="localhost",
    help="DataDog StatsD host (default: localhost)",
)
@click.option(
    "--datadog-port",
    type=int,
    default=8125,
    help="DataDog StatsD port (default: 8125)",
)
@click.option(
    "--no-datadog",
    is_flag=True,
    help="Disable DataDog monitoring",
)
def validate(
    environment: str,
    database: Optional[str],
    log_level: str,
    datadog_host: str,
    datadog_port: int,
    no_datadog: bool,
) -> None:
    """Validate databases by comparing source and destination statistics.

    This matches the bash script's --validate-only mode. Compares table counts,
    row counts, function counts, and other database statistics without performing
    any migration.

    Examples:

        # Validate all databases
        rds-migrate validate --environment staging

        # Validate specific database
        rds-migrate validate --environment staging --database mydb

        # Validate with debug logging
        rds-migrate validate -e staging --log-level DEBUG
    """
    configure_logging(log_level=log_level)
    logger = get_logger(__name__)

    env = Environment(environment.lower())
    config = MigrationConfig.for_environment(env, specific_db=database)

    console.print("\n[bold]RDS Database Validation[/bold]")
    console.print(f"  Environment: {config.environment.value}")
    console.print(f"  Source: {config.source_env} (RDS ID: {config.source_rds_id})")
    console.print(f"  Destination: {config.destination_env} (RDS ID: {config.destination_rds_id})")
    console.print(f"  Database: {database or 'All (except excluded)'}")
    console.print()

    try:
        # Initialize migrator
        migrator = DatabaseMigrator(
            config,
            enable_datadog=not no_datadog,
            datadog_statsd_host=datadog_host,
            datadog_statsd_port=datadog_port,
        )

        # Test connections
        console.print("[bold]Testing database connections...[/bold]")
        if not migrator.test_connections():
            console.print("[red]Connection test failed.[/red]\n")
            sys.exit(1)
        console.print("[green]✓ Connection tests passed[/green]\n")

        # Run validation
        databases = [database] if database else None
        results = migrator.validate_databases(databases)

        # Print summary
        console.print("\n[bold]Validation Summary[/bold]")
        total = len(results)
        passed = sum(1 for is_valid, _ in results.values() if is_valid)
        failed = total - passed

        console.print(f"  Total: {total}")
        console.print(f"  [green]Passed: {passed}[/green]")
        console.print(f"  [red]Failed: {failed}[/red]\n")

        # Print details for failed validations
        if failed > 0:
            console.print("[bold red]Validation Failures:[/bold red]")
            for db_name, (is_valid, messages) in results.items():
                if not is_valid:
                    console.print(f"\n[yellow]{db_name}:[/yellow]")
                    for msg in messages:
                        console.print(f"  • {msg}")
            console.print()

        # Exit with error if any failed
        if failed > 0:
            sys.exit(1)

    except Exception as e:
        logger.error("Validation failed", error=str(e))
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        sys.exit(1)


@cli.command()
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["staging", "production"], case_sensitive=False),
    required=True,
    help="Target environment",
)
@click.option(
    "--database",
    "-d",
    required=True,
    help="Database name to get statistics for",
)
@click.option(
    "--source",
    is_flag=True,
    help="Get statistics from source database (default: destination)",
)
@click.option(
    "--tables",
    is_flag=True,
    help="Include table-level statistics",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level (default: INFO)",
)
@click.option(
    "--datadog-host",
    default="localhost",
    help="DataDog StatsD host (default: localhost)",
)
@click.option(
    "--datadog-port",
    type=int,
    default=8125,
    help="DataDog StatsD port (default: 8125)",
)
@click.option(
    "--no-datadog",
    is_flag=True,
    help="Disable DataDog monitoring",
)
def stats(
    environment: str,
    database: str,
    source: bool,
    tables: bool,
    log_level: str,
    datadog_host: str,
    datadog_port: int,
    no_datadog: bool,
) -> None:
    """Get database statistics including table counts, row counts, and more.

    Provides comprehensive statistics matching the bash script's get_db_stats function.

    Examples:

        # Get destination database statistics
        rds-migrate stats --environment staging --database mydb

        # Get source database statistics
        rds-migrate stats -e staging -d mydb --source

        # Include table-level statistics
        rds-migrate stats -e staging -d mydb --tables
    """
    configure_logging(log_level=log_level)
    logger = get_logger(__name__)

    env = Environment(environment.lower())
    config = MigrationConfig.for_environment(env)

    try:
        # Initialize migrator
        migrator = DatabaseMigrator(
            config,
            enable_datadog=not no_datadog,
            datadog_statsd_host=datadog_host,
            datadog_statsd_port=datadog_port,
        )

        # Select validator and database
        if source:
            validator = migrator.source_validator
            db_label = f"{config.source_env}"
        else:
            validator = migrator.dest_validator
            db_label = f"{config.destination_env}"

        console.print(f"\n[bold]Getting statistics for {database} on {db_label}[/bold]\n")

        # Get and print database statistics
        db_stats = validator.get_database_stats(database)
        validator.print_stats_table(db_stats)

        # Get and print table statistics if requested
        if tables:
            table_stats = validator.get_table_stats(database)

            if table_stats:
                table = Table(title=f"Table Statistics: {database}")
                table.add_column("Schema", style="cyan")
                table.add_column("Table Name", style="green")
                table.add_column("Row Count", style="blue", justify="right")
                table.add_column("Size (MB)", style="yellow", justify="right")
                table.add_column("Indexes", style="magenta", justify="right")

                for ts in table_stats:
                    size_mb = ts.size_bytes / 1024 / 1024
                    table.add_row(
                        ts.schema_name,
                        ts.table_name,
                        f"{ts.row_count:,}",
                        f"{size_mb:.2f}",
                        str(ts.index_count),
                    )

                console.print(table)
                console.print()

    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        sys.exit(1)


def _print_results_table(results: list) -> None:
    """Print migration results as a formatted table."""
    table = Table(title="Migration Results")
    table.add_column("Database", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Views Refreshed", style="blue")
    table.add_column("Size (MB)", style="magenta")
    table.add_column("Error", style="red")

    for result in results:
        status = "✓ Success" if result.success else "✗ Failed"
        status_style = "green" if result.success else "red"
        size_mb = result.size_bytes / 1024 / 1024 if result.size_bytes > 0 else 0

        table.add_row(
            result.database_name,
            f"[{status_style}]{status}[/{status_style}]",
            f"{result.duration_seconds:.2f}s",
            str(result.materialized_views_refreshed),
            f"{size_mb:.2f}",
            result.error or "",
        )

    console.print()
    console.print(table)
    console.print()


if __name__ == "__main__":
    cli()
