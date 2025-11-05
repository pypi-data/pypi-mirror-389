"""Materialized view detection, refresh, and validation."""

import time
from dataclasses import dataclass
from typing import Optional

from rds_migration.database import Database
from rds_migration.datadog import DataDogMonitor
from rds_migration.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MaterializedView:
    """Represents a PostgreSQL materialized view."""

    name: str
    schema: str
    definition: str
    has_indexes: bool
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None


class MaterializedViewManager:
    """Manager for materialized view operations with DataDog monitoring."""

    # Known materialized views with dependencies (order matters for refresh)
    KNOWN_VIEW_DEPENDENCIES = {
        "fulfillment_engine": [
            "tnm_facility_operating_times",  # Must be refreshed first
            "tnm_delivery_options",  # Depends on tnm_facility_operating_times
        ],
    }

    def __init__(
        self, database: Database, datadog_monitor: Optional[DataDogMonitor] = None
    ) -> None:
        """Initialize materialized view manager.

        Args:
            database: Database connection manager
            datadog_monitor: Optional DataDog monitor instance
        """
        self.database = database
        self.monitor = datadog_monitor
        logger.info("Materialized view manager initialized")

    def list_materialized_views(self, database_name: str) -> list[MaterializedView]:
        """List all materialized views in a database.

        Args:
            database_name: Database name

        Returns:
            List of MaterializedView objects
        """
        query = """
            SELECT
                schemaname as schema,
                matviewname as name,
                definition,
                hasindexes as has_indexes
            FROM pg_matviews
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, matviewname
        """

        logger.debug("Listing materialized views", database=database_name)
        results = self.database.execute_query(database_name, query)

        views = []
        for row in results:
            view = MaterializedView(
                name=row["name"],
                schema=row["schema"],
                definition=row["definition"],
                has_indexes=row["has_indexes"],
            )
            views.append(view)

        logger.info(
            "Found materialized views",
            database=database_name,
            count=len(views),
            views=[v.name for v in views],
        )

        if self.monitor:
            self.monitor.gauge(
                "materialized_views.count", len(views), tags=[f"database:{database_name}"]
            )

        return views

    def view_exists(self, database_name: str, view_name: str) -> bool:
        """Check if a materialized view exists.

        Args:
            database_name: Database name
            view_name: View name

        Returns:
            True if view exists, False otherwise
        """
        query = """
            SELECT 1
            FROM pg_matviews
            WHERE matviewname = %(view_name)s
        """

        results = self.database.execute_query(database_name, query, {"view_name": view_name})
        exists = len(results) > 0

        logger.debug(
            "Checked view existence", database=database_name, view=view_name, exists=exists
        )
        return exists

    def get_view_row_count(self, database_name: str, view_name: str) -> int:
        """Get row count for a materialized view.

        Args:
            database_name: Database name
            view_name: View name

        Returns:
            Row count
        """
        query = f"SELECT COUNT(*) FROM {view_name}"

        try:
            results = self.database.execute_query(database_name, query)
            count = results[0]["count"] if results else 0
            logger.debug(
                "Retrieved view row count", database=database_name, view=view_name, count=count
            )
            return count
        except Exception as e:
            logger.warning(
                "Failed to get view row count",
                database=database_name,
                view=view_name,
                error=str(e),
            )
            return 0

    def refresh_materialized_view(
        self, database_name: str, view_name: str, concurrent: bool = False
    ) -> tuple[bool, int, float]:
        """Refresh a materialized view.

        Args:
            database_name: Database name
            view_name: View name
            concurrent: Whether to use CONCURRENTLY option

        Returns:
            Tuple of (success, row_count, duration_seconds)
        """
        start_time = time.time()

        try:
            logger.info(
                "Refreshing materialized view",
                database=database_name,
                view=view_name,
                concurrent=concurrent,
            )

            # Build refresh command
            refresh_cmd = "REFRESH MATERIALIZED VIEW"
            if concurrent:
                refresh_cmd += " CONCURRENTLY"
            refresh_cmd += f" {view_name}"

            # Trace with DataDog
            if self.monitor:
                with self.monitor.trace_operation(
                    "materialized_view.refresh",
                    resource=view_name,
                    tags={
                        "database": database_name,
                        "view": view_name,
                        "concurrent": str(concurrent),
                    },
                ):
                    self.database.execute_command(database_name, refresh_cmd)
            else:
                self.database.execute_command(database_name, refresh_cmd)

            # Get row count after refresh
            row_count = self.get_view_row_count(database_name, view_name)

            duration = time.time() - start_time
            logger.info(
                "Materialized view refreshed successfully",
                database=database_name,
                view=view_name,
                rows=row_count,
                duration=duration,
            )

            if self.monitor:
                self.monitor.record_materialized_view_refresh(
                    database_name, view_name, row_count, duration
                )

            return True, row_count, duration

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Failed to refresh materialized view",
                database=database_name,
                view=view_name,
                error=str(e),
                duration=duration,
            )

            if self.monitor:
                self.monitor.increment_counter(
                    "materialized_view.refresh.failed",
                    tags=[f"database:{database_name}", f"view:{view_name}"],
                )

            return False, 0, duration

    def refresh_all_views(
        self, database_name: str, concurrent: bool = False
    ) -> dict[str, tuple[bool, int, float]]:
        """Refresh all materialized views in a database, respecting dependencies.

        Args:
            database_name: Database name
            concurrent: Whether to use CONCURRENTLY option

        Returns:
            Dictionary mapping view names to (success, row_count, duration) tuples
        """
        logger.info(
            "Refreshing all materialized views", database=database_name, concurrent=concurrent
        )

        # Get all views
        views = self.list_materialized_views(database_name)

        if not views:
            logger.info("No materialized views found", database=database_name)
            return {}

        results = {}

        # Check if database has known view dependencies
        db_name_lower = database_name.lower()
        known_deps = None
        for key, deps in self.KNOWN_VIEW_DEPENDENCIES.items():
            if key in db_name_lower:
                known_deps = deps
                break

        if known_deps:
            # Refresh views in dependency order
            logger.info(
                "Using known dependency order",
                database=database_name,
                order=known_deps,
            )

            # First refresh views in dependency order
            for view_name in known_deps:
                if any(v.name == view_name for v in views):
                    success, row_count, duration = self.refresh_materialized_view(
                        database_name, view_name, concurrent
                    )
                    results[view_name] = (success, row_count, duration)

            # Then refresh any remaining views
            remaining_views = [v for v in views if v.name not in known_deps]
            for view in remaining_views:
                success, row_count, duration = self.refresh_materialized_view(
                    database_name, view.name, concurrent
                )
                results[view.name] = (success, row_count, duration)

        else:
            # No known dependencies, refresh all views in alphabetical order
            logger.info(
                "No known dependencies, refreshing in alphabetical order", database=database_name
            )
            for view in views:
                success, row_count, duration = self.refresh_materialized_view(
                    database_name, view.name, concurrent
                )
                results[view.name] = (success, row_count, duration)

        # Log summary
        total_views = len(results)
        successful = sum(1 for success, _, _ in results.values() if success)
        failed = total_views - successful

        logger.info(
            "Materialized views refresh completed",
            database=database_name,
            total=total_views,
            successful=successful,
            failed=failed,
        )

        if self.monitor:
            self.monitor.gauge(
                "materialized_views.refresh.total",
                total_views,
                tags=[f"database:{database_name}"],
            )
            self.monitor.gauge(
                "materialized_views.refresh.successful",
                successful,
                tags=[f"database:{database_name}"],
            )
            self.monitor.gauge(
                "materialized_views.refresh.failed",
                failed,
                tags=[f"database:{database_name}"],
            )

        return results

    def validate_view_data(self, database_name: str, view_name: str) -> tuple[bool, str]:
        """Validate that a materialized view has data.

        Args:
            database_name: Database name
            view_name: View name

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Check if view exists
            if not self.view_exists(database_name, view_name):
                return False, f"View {view_name} does not exist"

            # Check row count
            row_count = self.get_view_row_count(database_name, view_name)

            if row_count == 0:
                return False, f"View {view_name} exists but has 0 rows"

            logger.info(
                "View validation successful",
                database=database_name,
                view=view_name,
                rows=row_count,
            )
            return True, f"View {view_name} is valid with {row_count} rows"

        except Exception as e:
            error_msg = f"View validation failed: {str(e)}"
            logger.error(
                "View validation failed", database=database_name, view=view_name, error=str(e)
            )
            return False, error_msg

    def get_view_dependencies(self, database_name: str, view_name: str) -> list[str]:
        """Get dependencies for a materialized view.

        Args:
            database_name: Database name
            view_name: View name

        Returns:
            List of dependent table/view names
        """
        query = """
            SELECT DISTINCT
                ref_nsp.nspname || '.' || ref_cl.relname AS dependency
            FROM pg_depend d
            JOIN pg_rewrite r ON r.oid = d.objid
            JOIN pg_class c ON c.oid = r.ev_class
            JOIN pg_namespace nsp ON nsp.oid = c.relnamespace
            JOIN pg_class ref_cl ON ref_cl.oid = d.refobjid
            JOIN pg_namespace ref_nsp ON ref_nsp.oid = ref_cl.relnamespace
            WHERE c.relkind = 'm'
                AND c.relname = %(view_name)s
                AND d.deptype = 'n'
                AND ref_cl.relkind IN ('r', 'm', 'v')
            ORDER BY dependency
        """

        try:
            results = self.database.execute_query(database_name, query, {"view_name": view_name})
            dependencies = [row["dependency"] for row in results]

            logger.debug(
                "Retrieved view dependencies",
                database=database_name,
                view=view_name,
                dependencies=dependencies,
            )
            return dependencies

        except Exception as e:
            logger.warning(
                "Failed to get view dependencies",
                database=database_name,
                view=view_name,
                error=str(e),
            )
            return []

    def should_refresh_views(self, database_name: str) -> bool:
        """Determine if a database should have materialized views refreshed.

        Args:
            database_name: Database name

        Returns:
            True if database contains materialized views that should be refreshed
        """
        views = self.list_materialized_views(database_name)
        should_refresh = len(views) > 0

        logger.debug(
            "Checked if views should be refreshed",
            database=database_name,
            has_views=should_refresh,
            view_count=len(views),
        )

        return should_refresh
