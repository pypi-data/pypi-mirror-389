# RDS Migration Library

A production-grade Python library for migrating AWS RDS PostgreSQL databases with comprehensive support for materialized views, connection management, validation, and DataDog monitoring.

## Features

- **Database Migration**: Dump and restore PostgreSQL databases using `pg_dump` and `pg_restore`
- **Materialized Views**: Automatic detection, dependency resolution, and concurrent refresh
- **Connection Management**: Pre-flight testing, active connection termination, role password rotation
- **Validation**: Comprehensive pre/post-migration validation with statistics comparison
- **Statistics Collection**: Database and table-level metrics (row counts, sizes, indexes, functions, sequences, triggers)
- **DataDog Integration**: All operations send metrics and traces to DataDog
- **Type-Safe**: Full type hints throughout the codebase
- **OOP Design**: Modular classes that can be used independently or composed

## Installation

```bash
# Install dependencies
poetry install

# Or using pip
pip install -r requirements.txt
```

## Quick Start

### CLI Usage

```bash
# Migrate all databases in staging
rds-migrate migrate --environment staging

# Migrate specific database
rds-migrate migrate -e staging --database mydb

# Dry run (see what would be done)
rds-migrate migrate -e staging --dry-run

# Pre-migration validation
rds-migrate validate -e staging

# Get database statistics
rds-migrate stats -e staging -d mydb --tables

# List materialized views
rds-migrate list-views -e staging -d mydb

# Refresh materialized views
rds-migrate refresh-views -e staging -d mydb
```

### Library Usage

```python
from rds_migration import (
    MigrationConfig,
    DatabaseMigrator,
    ConnectionManager,
    DatabaseValidator,
    Database,
    RDSConfig,
)

# Initialize configuration
config = MigrationConfig.for_environment("staging")

# Full migration with all features
migrator = DatabaseMigrator(config)
results = migrator.migrate_all()

# Or use individual components
from rds_migration.datadog import DataDogMonitor

# Connection management only
monitor = DataDogMonitor(enabled=True, environment="staging")
rds_config = RDSConfig(
    rds_id="db-XXX",
    endpoint="mydb.us-east-1.rds.amazonaws.com",
    password="secret",
)
db = Database(rds_config, monitor)
conn_manager = ConnectionManager(db, monitor)

# Test connection
if conn_manager.test_connection():
    print("Connection successful!")

# Get connection statistics
stats = conn_manager.get_connection_stats("mydb")
print(f"Active: {stats['active']}, Idle: {stats['idle']}")

# Terminate connections for a role
terminated = conn_manager.terminate_connections("mydb", role_name="app_user")
print(f"Terminated {terminated} connections")

# Validation only
validator = DatabaseValidator(db, monitor)
db_stats = validator.get_database_stats("mydb")
validator.print_stats_table(db_stats)

# Compare source and destination
source_stats = validator.get_database_stats("mydb")
dest_stats = validator.get_database_stats("mydb")
is_valid, messages = validator.validate_migration("mydb", source_stats, dest_stats)
```

## CLI Commands

### `migrate`

Migrate databases from source to destination RDS instance.

**Options:**
- `--environment, -e`: Target environment (staging/production)
- `--database, -d`: Specific database to migrate (optional)
- `--dry-run`: Show what would be done without executing
- `--no-refresh-views`: Skip materialized view refresh
- `--work-dir`: Directory for SQL dumps (default: ./sql)
- `--log-level`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `--datadog-host`: DataDog StatsD host
- `--datadog-port`: DataDog StatsD port
- `--no-datadog`: Disable DataDog monitoring

**Examples:**
```bash
# Migrate all staging databases
rds-migrate migrate --environment staging

# Migrate specific database in production
rds-migrate migrate --environment production --database fulfillment_engine

# Dry run with debug logging
rds-migrate migrate -e staging --dry-run --log-level DEBUG
```

### `validate`

Validate databases by comparing source and destination statistics without performing migration.

**Options:**
- `--environment, -e`: Target environment (staging/production)
- `--database, -d`: Specific database to validate (optional)
- `--log-level`: Logging level
- `--datadog-host`: DataDog StatsD host
- `--datadog-port`: DataDog StatsD port
- `--no-datadog`: Disable DataDog monitoring

**Examples:**
```bash
# Validate all databases
rds-migrate validate --environment staging

# Validate specific database
rds-migrate validate -e staging -d mydb
```

**Validation Checks:**
- Table count matching
- Row count matching (allows 5% variance)
- View and materialized view counts
- Function, sequence, and trigger counts
- Database size comparison

### `stats`

Get comprehensive database statistics including table counts, row counts, functions, sequences, triggers, and size.

**Options:**
- `--environment, -e`: Target environment
- `--database, -d`: Database name (required)
- `--source`: Get stats from source database (default: destination)
- `--tables`: Include table-level statistics
- `--log-level`: Logging level
- `--datadog-host`: DataDog StatsD host
- `--datadog-port`: DataDog StatsD port
- `--no-datadog`: Disable DataDog monitoring

**Examples:**
```bash
# Get destination database statistics
rds-migrate stats -e staging -d mydb

# Get source database statistics with table details
rds-migrate stats -e staging -d mydb --source --tables
```

### `list-views`

List all materialized views in a database with their properties.

**Options:**
- `--environment, -e`: Target environment
- `--database, -d`: Database name (required)
- `--datadog-host`: DataDog StatsD host
- `--datadog-port`: DataDog StatsD port
- `--no-datadog`: Disable DataDog monitoring

**Example:**
```bash
rds-migrate list-views -e staging -d fulfillment_engine
```

### `refresh-views`

Refresh materialized views in a database with dependency resolution.

**Options:**
- `--environment, -e`: Target environment
- `--database, -d`: Database name (required)
- `--view, -v`: Specific view to refresh (optional)
- `--concurrent`: Use REFRESH MATERIALIZED VIEW CONCURRENTLY

**Examples:**
```bash
# Refresh all views
rds-migrate refresh-views -e staging -d fulfillment_engine

# Refresh specific view
rds-migrate refresh-views -e staging -d fulfillment_engine -v my_view

# Concurrent refresh (requires unique index)
rds-migrate refresh-views -e staging -d fulfillment_engine --concurrent
```

## Library Architecture

### Core Components

#### `DatabaseMigrator`
Main orchestrator that coordinates the entire migration process.

```python
from rds_migration import MigrationConfig, DatabaseMigrator

config = MigrationConfig.for_environment("staging")
migrator = DatabaseMigrator(config, enable_datadog=True)

# Test connections before migration
if migrator.test_connections():
    # Validate databases
    results = migrator.validate_databases()

    # Perform migration
    results = migrator.migrate_all()
```

#### `ConnectionManager`
Manages database connections, termination, and role password rotation.

```python
from rds_migration import ConnectionManager, Database, RDSConfig

db = Database(RDSConfig(...))
conn_manager = ConnectionManager(db)

# Test connection
conn_manager.test_connection()

# Get active connections
connections = conn_manager.get_active_connections("mydb", role_name="app_user")

# Terminate connections
count = conn_manager.terminate_connections("mydb", role_name="app_user", wait_seconds=10)

# Rotate password and terminate
success, count = conn_manager.terminate_and_rotate("mydb", "app_user")

# Get connection statistics
stats = conn_manager.get_connection_stats("mydb")
```

#### `DatabaseValidator`
Collects statistics and validates migrations.

```python
from rds_migration import DatabaseValidator, Database

validator = DatabaseValidator(Database(...))

# Get database statistics
stats = validator.get_database_stats("mydb")
print(f"Tables: {stats.table_count}, Rows: {stats.total_row_count}")

# Get table-level statistics
table_stats = validator.get_table_stats("mydb")
for ts in table_stats:
    print(f"{ts.table_name}: {ts.row_count} rows")

# Validate migration
is_valid, messages = validator.validate_migration("mydb", source_stats, dest_stats)

# Print formatted tables
validator.print_stats_table(stats)
validator.print_comparison_table("mydb", source_stats, dest_stats)
```

#### `MaterializedViewManager`
Manages materialized view detection, dependency resolution, and refresh.

```python
from rds_migration import MaterializedViewManager, Database

view_manager = MaterializedViewManager(Database(...))

# List views
views = view_manager.list_materialized_views("mydb")

# Check if refresh is needed
if view_manager.should_refresh_views("mydb"):
    # Refresh all views with dependency resolution
    results = view_manager.refresh_all_views("mydb", concurrent=False)

    # Refresh specific view
    success, rows, duration = view_manager.refresh_materialized_view("mydb", "my_view")
```

### Configuration

Configuration is managed through the `MigrationConfig` class with environment-specific presets.

```python
from rds_migration.config import MigrationConfig, Environment

# Use environment preset
config = MigrationConfig.for_environment(Environment.STAGING)

# Or create custom configuration
config = MigrationConfig(
    environment=Environment.STAGING,
    source_rds_id="db-XXX",
    destination_rds_id="db-YYY",
    source_env="staging",
    destination_env="staging-v2",
    excluded_databases=["rdsadmin", "template0"],
    refresh_materialized_views=True,
    work_dir="./sql",
    dry_run=False,
)
```

## DataDog Monitoring

All operations send metrics and traces to DataDog under the service name `databaseMigrationLibrary`.

### Metrics

**Database Operations:**
- `database.connection.duration.seconds` - Connection establishment time
- `database.query.duration.seconds` - Query execution time
- `database.command.duration.seconds` - Command execution time
- `database.dump.duration.seconds` - pg_dump duration
- `database.dump.size.bytes` - Dump file size
- `database.restore.duration.seconds` - pg_restore duration
- `database.vacuum.duration.seconds` - VACUUM ANALYZE duration

**Connection Management:**
- `connections.active` - Active connections
- `connections.idle` - Idle connections
- `connections.idle_in_transaction` - Idle in transaction
- `connections.total` - Total connections
- `connections.terminated` - Terminated connections

**Validation:**
- `validation.completed` - Validation runs (tagged with status)
- `validation.errors` - Number of validation errors
- `validation.warnings` - Number of validation warnings
- `database.table_count` - Number of tables
- `database.view_count` - Number of views
- `database.total_row_count` - Total row count
- `database.size_bytes` - Database size

**Migration:**
- `migration.started` - Migration initiated
- `migration.completed` - Successful migration
- `migration.failed` - Failed migration
- `migration.duration.seconds` - Total migration time

**Materialized Views:**
- `materialized_views.total` - Total views in database
- `materialized_views.refresh.started` - Refresh initiated
- `materialized_views.refresh.completed` - Successful refresh
- `materialized_views.refresh.failed` - Failed refresh
- `materialized_views.refresh.duration.seconds` - Refresh duration
- `materialized_views.refresh.rows` - Rows in refreshed view

### Traces

Distributed traces are created for:
- `database.connect` - Database connections
- `database.query` - Query execution
- `database.command` - Command execution
- `database.dump` - pg_dump operations
- `database.restore` - pg_restore operations
- `database.vacuum_analyze` - VACUUM ANALYZE
- `connections.terminate` - Connection termination
- `materialized_views.refresh` - View refresh

### Tags

All metrics and traces include relevant tags:
- `environment`: Environment name (staging, production)
- `database`: Database name
- `source`: Source environment/RDS
- `destination`: Destination environment/RDS
- `status`: Operation status (success, failure, error)
- `role`: Role name (for connection operations)
- `view`: View name (for materialized view operations)

## Environment Variables

```bash
# AWS Configuration
AWS_PROFILE=staging
AWS_REGION=us-east-1

# DataDog Configuration (optional)
DD_AGENT_HOST=localhost
DD_AGENT_PORT=8125
```

## Configuration Files

### Excluded Databases

By default, the following databases are excluded from migration:
- `postgres` (system database)
- `rdsadmin` (AWS RDS management)
- `template0` (PostgreSQL template)
- `template1` (PostgreSQL template)

### SSM Parameter Store

Passwords are retrieved from AWS SSM Parameter Store using the pattern:
```
/${environment}/applications/wms/rds/BU_SHARED_PG_PASSWORD
```

For example:
- Staging: `/staging/applications/wms/rds/BU_SHARED_PG_PASSWORD`
- Production: `/production/applications/wms/rds/BU_SHARED_PG_PASSWORD`

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rds_migration

# Run specific test file
pytest tests/test_migration.py
```

### Code Quality

```bash
# Type checking
mypy rds_migration/

# Linting
ruff check rds_migration/

# Formatting
black rds_migration/
```

## Comparison to Bash Script

This Python library matches and exceeds the capabilities of the original bash script:

| Feature | Bash Script | Python Library |
|---------|-------------|----------------|
| Database Migration | ✅ | ✅ |
| Materialized Views | ✅ | ✅ (with dependency resolution) |
| Connection Management | ✅ | ✅ |
| Validation Mode | ✅ | ✅ |
| Statistics Collection | ✅ | ✅ (enhanced) |
| Role Management | ✅ | ✅ |
| DataDog Monitoring | ❌ | ✅ |
| Type Safety | ❌ | ✅ |
| Modular Design | ❌ | ✅ |
| Library Usage | ❌ | ✅ |
| CLI Commands | Basic | Rich with multiple commands |
| Error Handling | Basic | Comprehensive |
| Logging | Echo statements | Structured logging |
| Testing | Manual | Automated tests |

### Key Advantages

1. **Modularity**: Individual components can be used independently
2. **Type Safety**: Full type hints for better IDE support and fewer bugs
3. **DataDog Integration**: Comprehensive metrics and tracing
4. **Better Error Handling**: Structured exceptions with detailed context
5. **Rich Output**: Beautiful terminal tables using Rich library
6. **Dry Run Support**: See what would happen without executing
7. **Flexible Configuration**: Environment-specific presets with override support
8. **Library + CLI**: Can be used as both a library and command-line tool

## Troubleshooting

### Connection Issues

```bash
# Test connections before migration
rds-migrate validate -e staging

# Check connection statistics
rds-migrate stats -e staging -d mydb
```

### Materialized View Dependencies

If materialized view refresh fails due to dependencies:

```bash
# List all views to see dependencies
rds-migrate list-views -e staging -d mydb

# Refresh views one at a time
rds-migrate refresh-views -e staging -d mydb -v view1
```

### Validation Failures

```bash
# Compare source and destination statistics
rds-migrate stats -e staging -d mydb --source
rds-migrate stats -e staging -d mydb

# Run validation to see detailed differences
rds-migrate validate -e staging -d mydb
```

## License

MIT License

## Author

Architected and Coded by Arty Art (arthur.mandel@external.freshrealm.com)  and Matty Matt (matthew.ford@external.freshrealm.com
