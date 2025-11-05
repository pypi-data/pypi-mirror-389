# Open Source Tools

[![PyPI version](https://badge.fury.io/py/rds-migration-toolkit.svg)](https://badge.fury.io/py/rds-migration-toolkit)
[![Python Versions](https://img.shields.io/pypi/pyversions/rds-migration-toolkit.svg)](https://pypi.org/project/rds-migration-toolkit/)
[![Tests](https://github.com/arthur-mandel-freshRealm/openSourceTools/actions/workflows/test.yml/badge.svg)](https://github.com/arthur-mandel-freshRealm/openSourceTools/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Collection of open-source tools and utilities.

## RDS Migration Toolkit

A production-grade Python library for migrating AWS RDS PostgreSQL databases with comprehensive support for materialized views, connection management, validation, and DataDog monitoring.

### Installation

```bash
pip install rds-migration-toolkit
```

### Quick Start

```bash
# Migrate all databases in staging
rds-migrate migrate --environment staging

# Validate databases
rds-migrate validate --environment staging

# Get database statistics
rds-migrate stats -e staging -d mydb --tables
```

### Features

- **Database Migration**: Dump and restore PostgreSQL databases using `pg_dump` and `pg_restore`
- **Materialized Views**: Automatic detection, dependency resolution, and concurrent refresh
- **Connection Management**: Pre-flight testing, active connection termination, role password rotation
- **Validation**: Comprehensive pre/post-migration validation with statistics comparison
- **Statistics Collection**: Database and table-level metrics (row counts, sizes, indexes, functions, sequences, triggers)
- **DataDog Integration**: All operations send metrics and traces to DataDog
- **Type-Safe**: Full type hints throughout the codebase
- **OOP Design**: Modular classes that can be used independently or composed

### Documentation

See the [RDS Migration README](rds_migration/README.md) for detailed documentation.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Architected and Coded by Arty Art (arthur.mandel@external.freshrealm.com) and Matty Matt (matthew.ford@external.freshrealm.com)
