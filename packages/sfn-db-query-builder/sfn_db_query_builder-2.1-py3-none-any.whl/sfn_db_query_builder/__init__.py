"""
Multi-Database Query Builder

A professional, maintainable query builder for multiple database systems.
Provides a unified interface for SQL operations across Snowflake, PostgreSQL, BigQuery, and Redshift.
"""

from .core.factory import DatabaseQueryBuilderFactory, create_query_builder
from .config.database_types import DatabaseType

__version__ = "2.0.0"
__author__ = "StepFunction Team"

# Main exports for backward compatibility
__all__ = [
    # Core components
    "DatabaseQueryBuilderFactory",
    "create_query_builder",
    "DatabaseType",
    # Legacy function exports for backward compatibility
    "check_if_table_exists",
    "check_if_column_exists",
    "get_schemas_like_pattern",
    "fetch_column_name",
    "fetch_column_name_datatype",
    "fetch_single_column_name_datatype",
    "fetch_all_tables_in_schema",
    "fetch_all_views_in_schema",
    "fetch_table_type_in_schema",
    "enclose_reserved_keywords",
    "enclose_reserved_keywords_v2",
    "handle_reserved_keywords",
    "get_tables_under_schema",
    "mode_function",
    "median_function",
    "concat_function",
    "pivot_function",
    "trim_function",
    "split_function",
    "timestamp_to_date_function",
    "substring_function",
    "table_rename_query",
    "date_diff_in_hours",
    "date_substraction",
    # Legacy class interface
    "MultiDatabaseQueryBuilder",
    # Legacy constants
    "SNOWFLAKE",
    "POSTGRESQL",
    "BIGQUERY",
    "REDSHIFT",
    "SNOWFLAKE_RESERVED_KEYWORDS",
    "POSTGRESQL_RESERVED_KEYWORDS",
    "BIGQUERY_RESERVED_KEYWORDS",
    "REDSHIFT_RESERVED_KEYWORDS",
    "NUMERICAL_DATA_TYPES",
]

# Import functions and class from main entry point
from .multi_database_query_builder import (
    # Main class interface
    MultiDatabaseQueryBuilder,
    # Function interface
    check_if_table_exists,
    check_if_column_exists,
    get_schemas_like_pattern,
    fetch_column_name,
    fetch_column_name_datatype,
    fetch_single_column_name_datatype,
    fetch_all_tables_in_schema,
    fetch_all_views_in_schema,
    fetch_table_type_in_schema,
    enclose_reserved_keywords,
    enclose_reserved_keywords_v2,
    handle_reserved_keywords,
    get_tables_under_schema,
    mode_function,
    median_function,
    concat_function,
    pivot_function,
    trim_function,
    split_function,
    timestamp_to_date_function,
    substring_function,
    table_rename_query,
    date_diff_in_hours,
    date_substraction,
)

# Import legacy constants from config
from .config.constants import (
    SNOWFLAKE_RESERVED_KEYWORDS,
    REDSHIFT_RESERVED_KEYWORDS,
    BIGQUERY_RESERVED_KEYWORDS,
    NUMERICAL_DATA_TYPES,
)

# Legacy constants for backward compatibility
SNOWFLAKE = "snowflake"
POSTGRESQL = "postgresql"
BIGQUERY = "bigquery"
REDSHIFT = "redshift"
POSTGRESQL_RESERVED_KEYWORDS = REDSHIFT_RESERVED_KEYWORDS  # PostgreSQL and Redshift share keywords
