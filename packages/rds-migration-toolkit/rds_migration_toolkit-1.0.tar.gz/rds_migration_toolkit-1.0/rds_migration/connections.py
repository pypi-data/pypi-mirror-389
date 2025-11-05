"""Database connection management and termination."""

import time
from typing import Optional

from rds_migration.database import Database
from rds_migration.datadog import DataDogMonitor
from rds_migration.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages database connections, termination, and role management."""

    def __init__(
        self, database: Database, datadog_monitor: Optional[DataDogMonitor] = None
    ) -> None:
        """Initialize connection manager.

        Args:
            database: Database connection manager
            datadog_monitor: Optional DataDog monitor instance
        """
        self.database = database
        self.monitor = datadog_monitor
        logger.info("Connection manager initialized")

    def role_exists(self, database_name: str, role_name: str) -> bool:
        """Check if a role exists.

        Args:
            database_name: Database name
            role_name: Role name to check

        Returns:
            True if role exists, False otherwise
        """
        query = "SELECT 1 FROM pg_roles WHERE rolname = %(role_name)s"
        results = self.database.execute_query(database_name, query, {"role_name": role_name})
        exists = len(results) > 0

        logger.debug("Checked role existence", role=role_name, exists=exists)
        return exists

    def get_active_connections(
        self, database_name: str, role_name: Optional[str] = None
    ) -> list[dict]:
        """Get active connections to a database.

        Args:
            database_name: Database name
            role_name: Optional role name to filter by

        Returns:
            List of active connections
        """
        query = """
            SELECT pid, usename, datname, client_addr, application_name, state
            FROM pg_stat_activity
            WHERE pid <> pg_backend_pid()
            AND datname = %(database_name)s
        """

        params: dict = {"database_name": database_name}

        if role_name:
            query += " AND usename = %(role_name)s"
            params["role_name"] = role_name

        results = self.database.execute_query("postgres", query, params)

        logger.info(
            "Retrieved active connections",
            database=database_name,
            role=role_name,
            count=len(results),
        )

        return results

    def terminate_connections(
        self,
        database_name: str,
        role_name: Optional[str] = None,
        wait_seconds: int = 10,
    ) -> int:
        """Terminate active connections to a database.

        Args:
            database_name: Database name
            role_name: Optional role name to filter by
            wait_seconds: Seconds to wait before force termination

        Returns:
            Number of connections terminated
        """
        logger.info(
            "Terminating connections",
            database=database_name,
            role=role_name,
            wait_seconds=wait_seconds,
        )

        start_time = time.time()

        # Check active connections first
        connections = self.get_active_connections(database_name, role_name)

        if not connections:
            logger.info("No active connections to terminate")
            return 0

        logger.warning(
            f"Found {len(connections)} active connections, waiting {wait_seconds}s before termination",
            count=len(connections),
        )

        # Wait for connections to close naturally
        time.sleep(wait_seconds)

        # Build termination query
        terminate_query = """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE pid <> pg_backend_pid()
            AND datname = %(database_name)s
        """

        params: dict = {"database_name": database_name}

        if role_name:
            terminate_query += " AND usename = %(role_name)s"
            params["role_name"] = role_name

        # Terminate connections
        if self.monitor:
            with self.monitor.trace_operation(
                "connections.terminate",
                resource=database_name,
                tags={"database": database_name, "role": role_name or "all"},
            ):
                self.database.execute_command("postgres", terminate_query, params)
        else:
            self.database.execute_command("postgres", terminate_query, params)

        duration = time.time() - start_time

        logger.info(
            "Connections terminated",
            database=database_name,
            role=role_name,
            count=len(connections),
            duration=duration,
        )

        if self.monitor:
            self.monitor.gauge(
                "connections.terminated",
                len(connections),
                tags=[f"database:{database_name}", f"role:{role_name or 'all'}"],
            )

        return len(connections)

    def rotate_role_password(self, database_name: str, role_name: str, new_password: str) -> bool:
        """Rotate a role's password.

        Args:
            database_name: Database name
            role_name: Role name
            new_password: New password

        Returns:
            True if successful
        """
        logger.info("Rotating role password", role=role_name)

        # Check if role exists first
        if not self.role_exists(database_name, role_name):
            logger.warning("Role does not exist, skipping password rotation", role=role_name)
            return False

        try:
            # Use parameterized query safely - password needs special handling
            # psycopg3 doesn't support parameterizing identifiers or passwords in ALTER ROLE
            # So we'll use proper escaping
            from psycopg import sql

            query = sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                sql.Identifier(role_name), sql.Literal(new_password)
            )

            with self.database.connection(database_name) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    conn.commit()

            logger.info("Role password rotated successfully", role=role_name)
            return True

        except Exception as e:
            logger.error("Failed to rotate role password", role=role_name, error=str(e))
            return False

    def terminate_and_rotate(
        self, database_name: str, role_name: str, temp_password_prefix: str = "TEMP_PASS"
    ) -> tuple[bool, int]:
        """Terminate connections and rotate password for a role.

        This matches the bash script's approach of:
        1. Rotate password to temporary value
        2. Wait for connections to close
        3. Terminate any remaining connections

        Args:
            database_name: Database name
            role_name: Role name
            temp_password_prefix: Prefix for temporary password

        Returns:
            Tuple of (success, connections_terminated)
        """
        import secrets

        # Generate temporary password
        temp_password = f"{temp_password_prefix}_{int(time.time())}_{secrets.token_hex(8)}"

        logger.info("Starting connection termination and password rotation", role=role_name)

        # Rotate password first
        if not self.rotate_role_password(database_name, role_name, temp_password):
            return False, 0

        # Terminate connections
        count = self.terminate_connections(database_name, role_name, wait_seconds=10)

        return True, count

    def test_connection(self, database_name: str = "postgres") -> bool:
        """Test database connectivity.

        Args:
            database_name: Database name to test

        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = self.database.test_connection(database_name)

            if self.monitor:
                status_tag = "success" if result else "failure"
                self.monitor.increment_counter(
                    "connection.test",
                    tags=[f"database:{database_name}", f"status:{status_tag}"],
                )

            return result

        except Exception as e:
            logger.error("Connection test failed", database=database_name, error=str(e))

            if self.monitor:
                self.monitor.increment_counter(
                    "connection.test", tags=[f"database:{database_name}", "status:error"]
                )

            return False

    def get_connection_stats(self, database_name: str) -> dict[str, int]:
        """Get connection statistics for a database.

        Args:
            database_name: Database name

        Returns:
            Dictionary with connection statistics
        """
        query = """
            SELECT
                COUNT(*) FILTER (WHERE state = 'active') as active,
                COUNT(*) FILTER (WHERE state = 'idle') as idle,
                COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                COUNT(*) as total
            FROM pg_stat_activity
            WHERE datname = %(database_name)s
            AND pid <> pg_backend_pid()
        """

        results = self.database.execute_query("postgres", query, {"database_name": database_name})

        if results:
            stats = {
                "active": results[0]["active"] or 0,
                "idle": results[0]["idle"] or 0,
                "idle_in_transaction": results[0]["idle_in_transaction"] or 0,
                "total": results[0]["total"] or 0,
            }

            logger.debug("Retrieved connection stats", database=database_name, **stats)

            if self.monitor:
                for stat_name, value in stats.items():
                    self.monitor.gauge(
                        f"connections.{stat_name}",
                        value,
                        tags=[f"database:{database_name}"],
                    )

            return stats

        return {"active": 0, "idle": 0, "idle_in_transaction": 0, "total": 0}
