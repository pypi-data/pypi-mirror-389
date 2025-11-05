"""DataDog monitoring and metrics integration."""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Optional

from datadog import statsd
from ddtrace import tracer
from ddtrace.span import Span

from rds_migration.logger import get_logger

logger = get_logger(__name__)

# DataDog service name
SERVICE_NAME = "databaseMigrationLibrary"


class DataDogMonitor:
    """DataDog monitoring and metrics manager."""

    def __init__(
        self,
        enabled: bool = True,
        environment: str = "production",
        statsd_host: str = "localhost",
        statsd_port: int = 8125,
    ) -> None:
        """Initialize DataDog monitoring.

        Args:
            enabled: Whether DataDog monitoring is enabled
            environment: Environment name (staging, production)
            statsd_host: StatsD host address
            statsd_port: StatsD port
        """
        self.enabled = enabled
        self.environment = environment

        if self.enabled:
            try:
                # Configure StatsD
                statsd.host = statsd_host
                statsd.port = statsd_port
                statsd.namespace = SERVICE_NAME
                statsd.constant_tags = [f"env:{environment}"]

                # Configure tracer
                tracer.configure(
                    hostname=statsd_host,
                    port=statsd_port,
                    enabled=True,
                )

                logger.info(
                    "DataDog monitoring initialized",
                    service=SERVICE_NAME,
                    environment=environment,
                    statsd_host=statsd_host,
                    statsd_port=statsd_port,
                )
            except Exception as e:
                logger.warning("Failed to initialize DataDog monitoring", error=str(e))
                self.enabled = False

    @contextmanager
    def trace_operation(
        self, operation_name: str, resource: str = "", tags: Optional[dict[str, Any]] = None
    ) -> Iterator[Optional[Span]]:
        """Trace an operation with DataDog APM.

        Args:
            operation_name: Name of the operation (e.g., "database.migrate")
            resource: Resource being operated on (e.g., database name)
            tags: Additional tags for the span

        Yields:
            DataDog span object if enabled, None otherwise
        """
        if not self.enabled:
            yield None
            return

        span_tags = {
            "service": SERVICE_NAME,
            "env": self.environment,
        }
        if tags:
            span_tags.update(tags)

        with tracer.trace(operation_name, service=SERVICE_NAME, resource=resource) as span:
            for key, value in span_tags.items():
                span.set_tag(key, value)
            yield span

    def increment_counter(
        self, metric_name: str, value: int = 1, tags: Optional[list[str]] = None
    ) -> None:
        """Increment a counter metric.

        Args:
            metric_name: Name of the metric (e.g., "migration.database.count")
            value: Value to increment by (default: 1)
            tags: Additional tags for the metric
        """
        if not self.enabled:
            return

        try:
            statsd.increment(metric_name, value=value, tags=tags or [])
        except Exception as e:
            logger.warning("Failed to increment DataDog counter", metric=metric_name, error=str(e))

    def gauge(self, metric_name: str, value: float, tags: Optional[list[str]] = None) -> None:
        """Set a gauge metric.

        Args:
            metric_name: Name of the metric (e.g., "migration.duration.seconds")
            value: Gauge value
            tags: Additional tags for the metric
        """
        if not self.enabled:
            return

        try:
            statsd.gauge(metric_name, value, tags=tags or [])
        except Exception as e:
            logger.warning("Failed to set DataDog gauge", metric=metric_name, error=str(e))

    def histogram(self, metric_name: str, value: float, tags: Optional[list[str]] = None) -> None:
        """Record a histogram metric.

        Args:
            metric_name: Name of the metric (e.g., "migration.row_count")
            value: Value to record
            tags: Additional tags for the metric
        """
        if not self.enabled:
            return

        try:
            statsd.histogram(metric_name, value, tags=tags or [])
        except Exception as e:
            logger.warning("Failed to record DataDog histogram", metric=metric_name, error=str(e))

    @contextmanager
    def timed_operation(self, metric_name: str, tags: Optional[list[str]] = None) -> Iterator[None]:
        """Time an operation and send duration to DataDog.

        Args:
            metric_name: Name of the metric (e.g., "migration.database.duration")
            tags: Additional tags for the metric

        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.histogram(metric_name, duration, tags=tags)
            logger.debug(f"Operation {metric_name} took {duration:.2f}s", duration=duration)

    def record_migration_start(
        self, database_name: str, source_env: str, destination_env: str
    ) -> None:
        """Record the start of a database migration.

        Args:
            database_name: Name of the database being migrated
            source_env: Source environment
            destination_env: Destination environment
        """
        tags = [
            f"database:{database_name}",
            f"source:{source_env}",
            f"destination:{destination_env}",
        ]
        self.increment_counter("migration.started", tags=tags)
        logger.info(
            "Migration started", database=database_name, source=source_env, dest=destination_env
        )

    def record_migration_success(
        self,
        database_name: str,
        duration_seconds: float,
        rows_migrated: int,
        materialized_views_refreshed: int = 0,
    ) -> None:
        """Record successful migration completion.

        Args:
            database_name: Name of the database migrated
            duration_seconds: Total migration duration in seconds
            rows_migrated: Number of rows migrated
            materialized_views_refreshed: Number of materialized views refreshed
        """
        tags = [f"database:{database_name}", "status:success"]
        self.increment_counter("migration.completed", tags=tags)
        self.histogram("migration.duration.seconds", duration_seconds, tags=tags)
        self.gauge("migration.rows_migrated", rows_migrated, tags=tags)

        if materialized_views_refreshed > 0:
            self.gauge(
                "migration.materialized_views.refreshed", materialized_views_refreshed, tags=tags
            )

        logger.info(
            "Migration completed successfully",
            database=database_name,
            duration=duration_seconds,
            rows=rows_migrated,
            views_refreshed=materialized_views_refreshed,
        )

    def record_migration_failure(
        self, database_name: str, error: str, duration_seconds: float
    ) -> None:
        """Record migration failure.

        Args:
            database_name: Name of the database
            error: Error message
            duration_seconds: Duration before failure
        """
        tags = [f"database:{database_name}", "status:failure"]
        self.increment_counter("migration.failed", tags=tags)
        self.histogram("migration.failure.duration.seconds", duration_seconds, tags=tags)
        logger.error(
            "Migration failed", database=database_name, error=error, duration=duration_seconds
        )

    def record_materialized_view_refresh(
        self, database_name: str, view_name: str, row_count: int, duration_seconds: float
    ) -> None:
        """Record materialized view refresh.

        Args:
            database_name: Name of the database
            view_name: Name of the materialized view
            row_count: Number of rows in the view
            duration_seconds: Refresh duration
        """
        tags = [f"database:{database_name}", f"view:{view_name}"]
        self.increment_counter("materialized_view.refreshed", tags=tags)
        self.histogram("materialized_view.duration.seconds", duration_seconds, tags=tags)
        self.gauge("materialized_view.row_count", row_count, tags=tags)

        logger.info(
            "Materialized view refreshed",
            database=database_name,
            view=view_name,
            rows=row_count,
            duration=duration_seconds,
        )
