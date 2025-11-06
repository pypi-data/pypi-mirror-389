"""
Constants and configuration values for the multi-database query builder.

This module contains all the constants used throughout the query builder system,
including reserved keywords, data types, and other configuration values.
"""

from typing import List

# Reserved keywords for different database systems
REDSHIFT_RESERVED_KEYWORDS: List[str] = ["time", "timestamp"]
BIGQUERY_RESERVED_KEYWORDS: List[str] = []
SNOWFLAKE_RESERVED_KEYWORDS: List[str] = ["minus"]

# Numerical data types
NUMERICAL_DATA_TYPES: List[str] = [
    "smallint",
    "integer",
    "bigint",
    "decimal",
    "numeric",
    "real",
    "double precision",
    "smallserial",
    "serial",
    "bigserial",
    "int",
    "int2",
    "int4",
    "int8",
    "float",
    "float4",
    "float8",
    "money",
]

# String data types
STRING_DATA_TYPES: List[str] = [
    "varchar",
    "char",
    "text",
    "string",
    "character varying",
    "character",
    "nvarchar",
    "nchar",
    "ntext",
]

# Date and time data types
DATETIME_DATA_TYPES: List[str] = [
    "date",
    "time",
    "timestamp",
    "timestamptz",
    "datetime",
    "datetime2",
    "smalldatetime",
    "datetimeoffset",
]

# Boolean data types
BOOLEAN_DATA_TYPES: List[str] = [
    "boolean",
    "bool",
    "bit",
]

# Default filter values
DEFAULT_FILTER_VALUES: List[str] = ["fivetran", "system", "internal"]

# SQL function categories
FUNCTION_CATEGORIES = {
    "AGGREGATE": ["mode", "median", "count", "sum", "avg", "min", "max"],
    "STRING": ["concat", "trim", "split", "substring", "upper", "lower"],
    "DATE": ["timestamp_to_date", "date_diff", "date_subtraction"],
    "MATH": ["abs", "round", "floor", "ceil", "sqrt"],
    "CONDITIONAL": ["case", "coalesce", "nullif", "ifnull"],
}

# Query builder settings
DEFAULT_QUERY_TIMEOUT = 30  # seconds
DEFAULT_MAX_ROWS = 1000
DEFAULT_BATCH_SIZE = 100

# Error messages
ERROR_MESSAGES = {
    "UNSUPPORTED_DATABASE": "Unsupported database type: {database_type}",
    "INVALID_PARAMETERS": "Invalid parameters provided: {details}",
    "QUERY_EXECUTION_FAILED": "Query execution failed: {error}",
    "CONNECTION_FAILED": "Database connection failed: {error}",
    "SCHEMA_NOT_FOUND": "Schema not found: {schema_name}",
    "TABLE_NOT_FOUND": "Table not found: {table_name}",
    "COLUMN_NOT_FOUND": "Column not found: {column_name}",
}

# Logging configuration
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "SLOW_QUERY_THRESHOLD": 5.0,  # seconds
    "LARGE_RESULT_THRESHOLD": 10000,  # rows
    "MEMORY_WARNING_THRESHOLD": 100 * 1024 * 1024,  # 100MB
}
