"""Database validation and statistics collection."""

from dataclasses import dataclass
from typing import Optional

from rich.console import Console
from rich.table import Table

from rds_migration.database import Database
from rds_migration.datadog import DataDogMonitor
from rds_migration.logger import get_logger

logger = get_logger(__name__)
console = Console()


@dataclass
class DatabaseStats:
    """Statistics for a single database."""

    database_name: str
    table_count: int
    view_count: int
    materialized_view_count: int
    function_count: int
    sequence_count: int
    trigger_count: int
    total_row_count: int
    size_bytes: int

    @property
    def size_mb(self) -> float:
        """Database size in megabytes."""
        return self.size_bytes / 1024 / 1024

    @property
    def size_gb(self) -> float:
        """Database size in gigabytes."""
        return self.size_bytes / 1024 / 1024 / 1024


@dataclass
class TableStats:
    """Statistics for a single table."""

    schema_name: str
    table_name: str
    row_count: int
    size_bytes: int
    index_count: int


class DatabaseValidator:
    """Validates databases and collects statistics."""

    def __init__(
        self, database: Database, datadog_monitor: Optional[DataDogMonitor] = None
    ) -> None:
        """Initialize database validator.

        Args:
            database: Database connection manager
            datadog_monitor: Optional DataDog monitor instance
        """
        self.database = database
        self.monitor = datadog_monitor
        logger.info("Database validator initialized")

    def get_database_stats(self, database_name: str) -> DatabaseStats:
        """Get comprehensive statistics for a database.

        Args:
            database_name: Database name

        Returns:
            DatabaseStats object
        """
        logger.info("Collecting database statistics", database=database_name)

        # Get all stats in one query for efficiency
        query = """
            SELECT
                (SELECT COUNT(*) FROM information_schema.tables
                 WHERE table_schema = 'public' AND table_type = 'BASE TABLE') as table_count,

                (SELECT COUNT(*) FROM information_schema.views
                 WHERE table_schema = 'public') as view_count,

                (SELECT COUNT(*) FROM pg_matviews
                 WHERE schemaname = 'public') as materialized_view_count,

                (SELECT COUNT(*) FROM pg_proc p
                 JOIN pg_namespace n ON p.pronamespace = n.oid
                 WHERE n.nspname = 'public') as function_count,

                (SELECT COUNT(*) FROM pg_class c
                 JOIN pg_namespace n ON c.relnamespace = n.oid
                 WHERE n.nspname = 'public' AND c.relkind = 'S') as sequence_count,

                (SELECT COUNT(*) FROM pg_trigger t
                 JOIN pg_class c ON t.tgrelid = c.oid
                 JOIN pg_namespace n ON c.relnamespace = n.oid
                 WHERE n.nspname = 'public' AND NOT t.tgisinternal) as trigger_count,

                pg_database_size(current_database()) as size_bytes
        """

        results = self.database.execute_query(database_name, query)

        if not results:
            raise ValueError(f"Failed to collect statistics for {database_name}")

        row = results[0]

        # Get total row count across all tables
        total_row_count = self._get_total_row_count(database_name)

        stats = DatabaseStats(
            database_name=database_name,
            table_count=row["table_count"] or 0,
            view_count=row["view_count"] or 0,
            materialized_view_count=row["materialized_view_count"] or 0,
            function_count=row["function_count"] or 0,
            sequence_count=row["sequence_count"] or 0,
            trigger_count=row["trigger_count"] or 0,
            total_row_count=total_row_count,
            size_bytes=row["size_bytes"] or 0,
        )

        logger.info(
            "Database statistics collected",
            database=database_name,
            tables=stats.table_count,
            rows=stats.total_row_count,
            size_mb=f"{stats.size_mb:.2f}",
        )

        # Send metrics to DataDog
        if self.monitor:
            self._send_stats_to_datadog(stats)

        return stats

    def _get_total_row_count(self, database_name: str) -> int:
        """Get total row count across all tables.

        Args:
            database_name: Database name

        Returns:
            Total row count
        """
        query = """
            SELECT SUM(n_live_tup) as total_rows
            FROM pg_stat_user_tables
        """

        results = self.database.execute_query(database_name, query)
        return results[0]["total_rows"] if results and results[0]["total_rows"] else 0

    def get_table_stats(self, database_name: str) -> list[TableStats]:
        """Get statistics for all tables in a database.

        Args:
            database_name: Database name

        Returns:
            List of TableStats objects
        """
        logger.info("Collecting table statistics", database=database_name)

        query = """
            SELECT
                schemaname as schema_name,
                tablename as table_name,
                n_live_tup as row_count,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = t.schemaname
                 AND tablename = t.tablename) as index_count
            FROM pg_stat_user_tables t
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC
        """

        results = self.database.execute_query(database_name, query)

        stats_list = []
        for row in results:
            stats = TableStats(
                schema_name=row["schema_name"],
                table_name=row["table_name"],
                row_count=row["row_count"] or 0,
                size_bytes=row["size_bytes"] or 0,
                index_count=row["index_count"] or 0,
            )
            stats_list.append(stats)

        logger.info(
            "Table statistics collected", database=database_name, table_count=len(stats_list)
        )

        return stats_list

    def validate_migration(
        self, database_name: str, source_stats: DatabaseStats, dest_stats: DatabaseStats
    ) -> tuple[bool, list[str]]:
        """Validate a migration by comparing source and destination statistics.

        Args:
            database_name: Database name
            source_stats: Statistics from source database
            dest_stats: Statistics from destination database

        Returns:
            Tuple of (is_valid, list of validation errors/warnings)
        """
        logger.info("Validating migration", database=database_name)

        errors = []
        warnings = []

        # Table count validation
        if source_stats.table_count != dest_stats.table_count:
            errors.append(
                f"Table count mismatch: source={source_stats.table_count}, "
                f"dest={dest_stats.table_count}"
            )

        # View count validation
        if source_stats.view_count != dest_stats.view_count:
            warnings.append(
                f"View count mismatch: source={source_stats.view_count}, "
                f"dest={dest_stats.view_count}"
            )

        # Materialized view count validation
        if source_stats.materialized_view_count != dest_stats.materialized_view_count:
            warnings.append(
                f"Materialized view count mismatch: source={source_stats.materialized_view_count}, "
                f"dest={dest_stats.materialized_view_count}"
            )

        # Function count validation
        if source_stats.function_count != dest_stats.function_count:
            warnings.append(
                f"Function count mismatch: source={source_stats.function_count}, "
                f"dest={dest_stats.function_count}"
            )

        # Row count validation (allow 5% variance for timing issues)
        row_diff_pct = (
            abs(source_stats.total_row_count - dest_stats.total_row_count)
            / max(source_stats.total_row_count, 1)
            * 100
        )

        if row_diff_pct > 5:
            errors.append(
                f"Row count mismatch ({row_diff_pct:.1f}%): source={source_stats.total_row_count}, "
                f"dest={dest_stats.total_row_count}"
            )
        elif row_diff_pct > 1:
            warnings.append(
                f"Minor row count difference ({row_diff_pct:.1f}%): "
                f"source={source_stats.total_row_count}, dest={dest_stats.total_row_count}"
            )

        is_valid = len(errors) == 0

        all_messages = errors + warnings

        if is_valid:
            logger.info(
                "Migration validation passed", database=database_name, warnings=len(warnings)
            )
        else:
            logger.error(
                "Migration validation failed",
                database=database_name,
                errors=len(errors),
                warnings=len(warnings),
            )

        # Send validation results to DataDog
        if self.monitor:
            status_tag = "success" if is_valid else "failure"
            self.monitor.increment_counter(
                "validation.completed",
                tags=[f"database:{database_name}", f"status:{status_tag}"],
            )
            self.monitor.gauge("validation.errors", len(errors), tags=[f"database:{database_name}"])
            self.monitor.gauge(
                "validation.warnings", len(warnings), tags=[f"database:{database_name}"]
            )

        return is_valid, all_messages

    def _send_stats_to_datadog(self, stats: DatabaseStats) -> None:
        """Send database statistics to DataDog.

        Args:
            stats: DatabaseStats object
        """
        if not self.monitor:
            return

        tags = [f"database:{stats.database_name}"]

        self.monitor.gauge("database.table_count", stats.table_count, tags=tags)
        self.monitor.gauge("database.view_count", stats.view_count, tags=tags)
        self.monitor.gauge(
            "database.materialized_view_count", stats.materialized_view_count, tags=tags
        )
        self.monitor.gauge("database.function_count", stats.function_count, tags=tags)
        self.monitor.gauge("database.sequence_count", stats.sequence_count, tags=tags)
        self.monitor.gauge("database.trigger_count", stats.trigger_count, tags=tags)
        self.monitor.gauge("database.total_row_count", stats.total_row_count, tags=tags)
        self.monitor.gauge("database.size_bytes", stats.size_bytes, tags=tags)

    def print_stats_table(self, stats: DatabaseStats) -> None:
        """Print database statistics as a formatted table.

        Args:
            stats: DatabaseStats object
        """
        table = Table(title=f"Database Statistics: {stats.database_name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Tables", str(stats.table_count))
        table.add_row("Views", str(stats.view_count))
        table.add_row("Materialized Views", str(stats.materialized_view_count))
        table.add_row("Functions", str(stats.function_count))
        table.add_row("Sequences", str(stats.sequence_count))
        table.add_row("Triggers", str(stats.trigger_count))
        table.add_row("Total Rows", f"{stats.total_row_count:,}")
        table.add_row("Size (MB)", f"{stats.size_mb:.2f}")
        table.add_row("Size (GB)", f"{stats.size_gb:.2f}")

        console.print()
        console.print(table)
        console.print()

    def print_comparison_table(
        self, database_name: str, source_stats: DatabaseStats, dest_stats: DatabaseStats
    ) -> None:
        """Print comparison of source and destination statistics.

        Args:
            database_name: Database name
            source_stats: Source database statistics
            dest_stats: Destination database statistics
        """
        table = Table(title=f"Migration Validation: {database_name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Source", style="blue", justify="right")
        table.add_column("Destination", style="green", justify="right")
        table.add_column("Match", style="yellow")

        def match_status(src: int, dst: int) -> str:
            return "✓" if src == dst else "✗"

        table.add_row(
            "Tables",
            str(source_stats.table_count),
            str(dest_stats.table_count),
            match_status(source_stats.table_count, dest_stats.table_count),
        )
        table.add_row(
            "Views",
            str(source_stats.view_count),
            str(dest_stats.view_count),
            match_status(source_stats.view_count, dest_stats.view_count),
        )
        table.add_row(
            "Materialized Views",
            str(source_stats.materialized_view_count),
            str(dest_stats.materialized_view_count),
            match_status(source_stats.materialized_view_count, dest_stats.materialized_view_count),
        )
        table.add_row(
            "Functions",
            str(source_stats.function_count),
            str(dest_stats.function_count),
            match_status(source_stats.function_count, dest_stats.function_count),
        )
        table.add_row(
            "Total Rows",
            f"{source_stats.total_row_count:,}",
            f"{dest_stats.total_row_count:,}",
            match_status(source_stats.total_row_count, dest_stats.total_row_count),
        )
        table.add_row("Size (MB)", f"{source_stats.size_mb:.2f}", f"{dest_stats.size_mb:.2f}", "")

        console.print()
        console.print(table)
        console.print()
