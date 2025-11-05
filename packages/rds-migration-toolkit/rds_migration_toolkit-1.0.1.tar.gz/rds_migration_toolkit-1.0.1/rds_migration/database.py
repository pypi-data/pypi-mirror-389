"""Database connection and management for RDS migrations."""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Optional

import boto3
import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from rds_migration.config import RDSConfig
from rds_migration.datadog import DataDogMonitor
from rds_migration.logger import get_logger

logger = get_logger(__name__)


class Database:
    """PostgreSQL database connection manager with DataDog monitoring."""

    def __init__(
        self,
        config: RDSConfig,
        datadog_monitor: Optional[DataDogMonitor] = None,
        connect_timeout: int = 30,
    ) -> None:
        """Initialize database connection manager.

        Args:
            config: RDS configuration
            datadog_monitor: Optional DataDog monitor instance
            connect_timeout: Connection timeout in seconds
        """
        self.config = config
        self.monitor = datadog_monitor
        self.connect_timeout = connect_timeout
        self._connection: Optional[Connection] = None

        logger.info(
            "Database manager initialized",
            endpoint=config.endpoint,
            port=config.port,
            user=config.user,
        )

    @staticmethod
    def _get_ssm_parameter(parameter_name: str) -> str:
        """Retrieve password from AWS SSM Parameter Store.

        Args:
            parameter_name: SSM parameter name

        Returns:
            Parameter value
        """
        logger.info("Retrieving password from SSM", parameter=parameter_name)
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return str(response["Parameter"]["Value"])

    @contextmanager
    def connection(self, database: str = "postgres") -> Iterator[Connection]:
        """Get a database connection with automatic cleanup.

        Args:
            database: Database name to connect to

        Yields:
            psycopg3 Connection object
        """
        conn = None
        start_time = time.time()

        try:
            # Build connection string
            conninfo = (
                f"host={self.config.endpoint} "
                f"port={self.config.port} "
                f"dbname={database} "
                f"user={self.config.user} "
                f"password={self.config.password} "
                f"connect_timeout={self.connect_timeout}"
            )

            logger.debug("Connecting to database", database=database, endpoint=self.config.endpoint)

            # Trace connection with DataDog
            if self.monitor:
                with self.monitor.trace_operation(
                    "database.connect",
                    resource=database,
                    tags={"database": database, "host": self.config.endpoint},
                ):
                    conn = psycopg.connect(conninfo, row_factory=dict_row)
            else:
                conn = psycopg.connect(conninfo, row_factory=dict_row)

            duration = time.time() - start_time
            logger.info("Database connection established", database=database, duration=duration)

            if self.monitor:
                self.monitor.histogram(
                    "database.connection.duration.seconds",
                    duration,
                    tags=[f"database:{database}"],
                )

            yield conn  # type: ignore[misc]

        except psycopg.Error as e:
            duration = time.time() - start_time
            logger.error(
                "Database connection failed",
                database=database,
                error=str(e),
                duration=duration,
            )
            if self.monitor:
                self.monitor.increment_counter(
                    "database.connection.failed", tags=[f"database:{database}"]
                )
            raise

        finally:
            if conn:
                try:
                    conn.close()
                    logger.debug("Database connection closed", database=database)
                except Exception as e:
                    logger.warning("Error closing database connection", error=str(e))

    def execute_query(
        self, database: str, query: str, params: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            database: Database name
            query: SQL query
            params: Query parameters

        Returns:
            List of result rows as dictionaries
        """
        start_time = time.time()

        with self.connection(database) as conn:
            with conn.cursor() as cur:
                logger.debug("Executing query", database=database, query=query[:100])

                if self.monitor:
                    with self.monitor.trace_operation(
                        "database.query",
                        resource=database,
                        tags={"database": database, "query_type": query.split()[0].upper()},
                    ):
                        cur.execute(query, params)
                        results = cur.fetchall()
                else:
                    cur.execute(query, params)
                    results = cur.fetchall()

                duration = time.time() - start_time
                logger.debug(
                    "Query executed",
                    database=database,
                    rows=len(results),
                    duration=duration,
                )

                if self.monitor:
                    self.monitor.histogram(
                        "database.query.duration.seconds",
                        duration,
                        tags=[f"database:{database}"],
                    )

                return results  # type: ignore[return-value]

    def execute_command(
        self, database: str, command: str, params: Optional[dict[str, Any]] = None
    ) -> None:
        """Execute a command (INSERT, UPDATE, DELETE, DDL) without returning results.

        Args:
            database: Database name
            command: SQL command
            params: Command parameters
        """
        start_time = time.time()

        with self.connection(database) as conn:
            with conn.cursor() as cur:
                logger.debug("Executing command", database=database, command=command[:100])

                if self.monitor:
                    with self.monitor.trace_operation(
                        "database.command",
                        resource=database,
                        tags={"database": database, "command_type": command.split()[0].upper()},
                    ):
                        cur.execute(command, params)
                        conn.commit()
                else:
                    cur.execute(command, params)
                    conn.commit()

                duration = time.time() - start_time
                logger.debug("Command executed", database=database, duration=duration)

                if self.monitor:
                    self.monitor.histogram(
                        "database.command.duration.seconds",
                        duration,
                        tags=[f"database:{database}"],
                    )

    def list_databases(self, exclude_system: bool = True) -> list[str]:
        """List all databases in the PostgreSQL cluster.

        Args:
            exclude_system: Whether to exclude system databases

        Returns:
            List of database names
        """
        query = """
            SELECT datname
            FROM pg_database
            WHERE datistemplate = false
        """

        if exclude_system:
            query += " AND datname NOT IN ('postgres', 'rdsadmin')"

        query += " ORDER BY datname"

        results = self.execute_query("postgres", query)
        databases = [row["datname"] for row in results]

        logger.info("Listed databases", count=len(databases))
        return databases

    def database_exists(self, database: str) -> bool:
        """Check if a database exists.

        Args:
            database: Database name

        Returns:
            True if database exists, False otherwise
        """
        query = "SELECT 1 FROM pg_database WHERE datname = %(database)s"
        results = self.execute_query("postgres", query, {"database": database})
        return len(results) > 0

    def get_database_size(self, database: str) -> int:
        """Get database size in bytes.

        Args:
            database: Database name

        Returns:
            Database size in bytes
        """
        query = "SELECT pg_database_size(%(database)s) as size"
        results = self.execute_query("postgres", query, {"database": database})
        return results[0]["size"] if results else 0

    def get_table_count(self, database: str) -> int:
        """Get number of tables in a database.

        Args:
            database: Database name

        Returns:
            Number of tables
        """
        query = """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """
        results = self.execute_query(database, query)
        return results[0]["count"] if results else 0

    def test_connection(self, database: str = "postgres") -> bool:
        """Test database connectivity.

        Args:
            database: Database name to test

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.connection(database) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    logger.info("Connection test successful", database=database)
                    return True
        except Exception as e:
            logger.error("Connection test failed", database=database, error=str(e))
            return False

    def get_server_version(self) -> str:
        """Get PostgreSQL server version.

        Returns:
            Server version string
        """
        results = self.execute_query("postgres", "SELECT version()")
        return results[0]["version"] if results else "Unknown"

    def vacuum_analyze(self, database: str) -> None:
        """Run VACUUM ANALYZE on a database.

        Args:
            database: Database name
        """
        logger.info("Running VACUUM ANALYZE", database=database)
        start_time = time.time()

        # VACUUM ANALYZE requires autocommit mode
        conninfo = (
            f"host={self.config.endpoint} "
            f"port={self.config.port} "
            f"dbname={database} "
            f"user={self.config.user} "
            f"password={self.config.password} "
            f"connect_timeout={self.connect_timeout}"
        )

        conn = psycopg.connect(conninfo, autocommit=True)
        try:
            with conn.cursor() as cur:
                if self.monitor:
                    with self.monitor.trace_operation(
                        "database.vacuum_analyze", resource=database, tags={"database": database}
                    ):
                        cur.execute("VACUUM ANALYZE")
                else:
                    cur.execute("VACUUM ANALYZE")

            duration = time.time() - start_time
            logger.info("VACUUM ANALYZE completed", database=database, duration=duration)

            if self.monitor:
                self.monitor.histogram(
                    "database.vacuum.duration.seconds", duration, tags=[f"database:{database}"]
                )
        finally:
            conn.close()
