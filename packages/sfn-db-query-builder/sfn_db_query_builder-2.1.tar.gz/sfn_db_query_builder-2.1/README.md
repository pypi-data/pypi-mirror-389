# Multi Database Query Builder

A powerful and flexible query builder for multiple databases with a clean, professional architecture.

## Overview

This package simplifies SQL query construction for various databases by offering a unified set of methods and operations. It abstracts database-specific syntax, allowing you to focus on crafting the logic of your queries rather than dealing with different database dialects.

**Supported Databases:**
- Snowflake
- PostgreSQL
- BigQuery
- Redshift

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Installation

To avoid conflicts with other packages, we recommend installing **multi-db-query-builder** within a virtual environment:

```
pip install multi-db-query-builder
```

## Requirements

1. **`data_store`**: Supported data stores are `snowflake`, `postgresql`, `bigquery`, `redshift`
2. **`db_session`**: Database session object

---

## Usage

### Basic Usage

```python
from sfn_db_query_builder import check_if_table_exists, mode_function, MultiDatabaseQueryBuilder

# Function interface - works with all databases
data_store = "snowflake"  # or "postgresql", "bigquery", "redshift"
db_session = "your_database_session"
schema_name = "your_schema_name"
table_name = "your_table_name"

# Check if a table exists
exists = check_if_table_exists(data_store, db_session, schema_name, table_name)
print(exists)  # True if exists, otherwise False

# Generate SQL functions
mode_sql = mode_function(data_store, "column_name", "alias_name")
print(mode_sql)  # Database-specific SQL for mode function
```

### Class Interface

```python
# Class interface - works with all databases
builder = MultiDatabaseQueryBuilder(data_store)
exists = builder.check_if_table_exists(db_session, schema_name, table_name)
mode_sql = builder.mode_function("column_name", "alias_name")
```

### Modern Service Layer (Future)

```python
# When ready, use the modern service layer
from sfn_db_query_builder.services import QueryService, FunctionService

query_service = QueryService(data_store)
exists = query_service.check_table_exists(db_session, schema_name, table_name)

function_service = FunctionService(data_store)
mode_sql = function_service.generate_mode_function("column_name", "alias_name")
```

---

## Architecture

The package follows a clean, professional architecture with:

### Core Components
- **`config/`**: Configuration management and database types
- **`core/`**: Core abstractions, interfaces, and factory patterns
- **`implementations/`**: Database-specific implementations

### Database Implementations
Each database has its own implementation with:
- Database-specific SQL generation
- Proper error handling
- Reserved keyword management

### Legacy Compatibility
- **100% Backward Compatible**: Existing code works unchanged
- **Unified Interface**: Single entry point for all databases
- **Database-Specific**: Each database handles its own functions

### How It Works
The package uses an **Abstract Factory Pattern** where:
1. User provides database type (e.g., "postgresql")
2. `MultiDatabaseQueryBuilder` creates the appropriate database-specific implementation
3. All method calls are delegated to the database-specific implementation
4. Database-specific SQL is generated and returned

**📊 [See detailed flow diagrams](PACKAGE_FLOW_DIAGRAM.md)** for visual representation of the architecture.

---

## API Reference

### Core Functions

#### Table Operations
- `check_if_table_exists(data_store, db_session, schema_name, table_name)` - Check if a table exists
- `check_if_column_exists(data_store, db_session, schema_name, table_name, column_name)` - Check if a column exists
- `fetch_column_name(data_store, db_session, schema_name, table_name)` - Get column names
- `fetch_column_name_datatype(data_store, db_session, schema_name, table_name, filter_val="")` - Get column names and types
- `fetch_single_column_name_datatype(data_store, db_session, schema_name, table_name, column_name)` - Get single column info
- `fetch_all_tables_in_schema(data_store, db_session, schema_name, pattern=None)` - Get all tables in schema
- `fetch_all_views_in_schema(data_store, db_session, schema_name, pattern=None)` - Get all views in schema
- `fetch_table_type_in_schema(data_store, db_session, schema_name, table_name)` - Get table type
- `get_tables_under_schema(data_store, db_session, schema)` - Get tables under schema
- `get_schemas_like_pattern(data_store, db_session, schema_name=None)` - Get schemas matching pattern

#### SQL Functions
- `mode_function(data_store, column, alias=None)` - Generate mode function SQL
- `median_function(data_store, column, alias=None)` - Generate median function SQL
- `concat_function(data_store, column, alias, separator)` - Generate concat function SQL
- `pivot_function(data_store, fields, column_list, schema, table_name)` - Generate pivot function SQL
- `trim_function(data_store, column, value, condition, alias=None)` - Generate trim function SQL
- `split_function(data_store, column, delimiter, part, alias=None)` - Generate split function SQL
- `timestamp_to_date_function(data_store, column, alias=None)` - Generate timestamp to date SQL
- `substring_function(data_store, column, start, end)` - Generate substring function SQL
- `date_diff_in_hours(data_store, start_date, end_date, table_name, alias)` - Generate date diff SQL
- `date_substraction(data_store, date_part, start_date, end_date, alias=None)` - Generate date subtraction SQL

#### Utility Functions
- `enclose_reserved_keywords(data_store, query)` - Enclose reserved keywords in query
- `enclose_reserved_keywords_v2(data_store, columns_string)` - Enclose reserved keywords in columns
- `handle_reserved_keywords(data_store, query_string)` - Handle reserved keywords
- `table_rename_query(data_store, schema_name, old_table_name, new_table_name)` - Generate table rename SQL

### Class Interface
- `MultiDatabaseQueryBuilder(data_store)` - Legacy class interface with all above methods

---

## Testing

The package includes comprehensive tests with meaningful, descriptive names:

### Test Structure
- **`test_main_entry_point.py`** - Tests the main entry point and public API (27 tests)
- **`test_core_components.py`** - Tests core infrastructure and components (25 tests)  
- **`test_database_implementations.py`** - Tests all database-specific implementations (39 tests)

### Test Coverage
- **Main Entry Point**: MultiDatabaseQueryBuilder class and function interfaces
- **Core Components**: Factory pattern, database types, configuration, error handling
- **Database Implementations**: PostgreSQL, BigQuery, Redshift, and Snowflake
- **Backward Compatibility**: Legacy function and class interfaces
- **Integration**: End-to-end workflows across all databases

Run tests:
```bash
pytest tests/ -v
```

**Total: 91 tests** covering all functionality with professional organization.

---

## Troubleshooting

### Common Issues

1. **Unsupported Data Source**: Check if the `data_store` is among the supported ones (`snowflake`, `postgresql`, `bigquery`, `redshift`).

2. **Import Errors**: Ensure you're importing from the correct module:
   ```python
   from sfn_db_query_builder import check_if_table_exists  # Correct
   from multi_database_query_builder import check_if_table_exists  # Legacy
   ```

3. **Database Session**: Ensure your `db_session` object is properly configured for your database.

### Error Handling

The package provides specific exception types:
- `UnsupportedDatabaseError`: For unsupported database types
- `QueryExecutionError`: For database query execution errors
- `ValidationError`: For input validation errors

---

## Migration Guide

### From Legacy to New Structure

The package maintains 100% backward compatibility. Your existing code will continue to work:

```python
# This still works
from multi_database_query_builder import check_if_table_exists

# But you can also use the new import
from sfn_db_query_builder import check_if_table_exists
```

### Future Migration Path

1. **Phase 1**: Continue using existing imports (no changes needed)
2. **Phase 2**: Update to new imports when convenient
3. **Phase 3**: Migrate to service layer for new features

---

## Conclusion

The **`multi-db-query-builder`** package provides a clean, professional, and maintainable solution for building database queries across multiple database systems. With its modern architecture, comprehensive testing, and 100% backward compatibility, it's ready for production use.

**Key Benefits:**
- ✅ **Database-Specific**: Each database handles its own logic
- ✅ **Self-Contained**: Each implementation is complete and independent
- ✅ **Unified Interface**: Single entry point for all databases
- ✅ **100% Backward Compatible**: Existing code works unchanged
- ✅ **Clean Architecture**: Professional structure with proper separation of concerns
- ✅ **Easy Maintenance**: Each database team can maintain their own functions
- ✅ **Future-Proof**: Easy to extend and migrate

Happy coding! 🚀
