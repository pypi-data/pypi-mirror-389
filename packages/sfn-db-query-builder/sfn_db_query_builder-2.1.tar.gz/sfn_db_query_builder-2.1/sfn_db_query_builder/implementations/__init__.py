"""
Database-specific implementations for the multi-database query builder.

This module contains all database-specific implementations of the query builder
interface, organized by database type, plus legacy function interfaces for
backward compatibility.
"""

from .base import BaseQueryBuilder
from .snowflake.sfn_db_query_builder import SnowflakeQueryBuilder
from .postgresql.sfn_db_query_builder import PostgresqlQueryBuilder
from .bigquery.sfn_db_query_builder import BigqueryQueryBuilder
from .redshift.sfn_db_query_builder import RedshiftQueryBuilder

# Core implementations only - no function interfaces here

# Legacy constants
from ..config.constants import (
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
POSTGRESQL_RESERVED_KEYWORDS = (
    REDSHIFT_RESERVED_KEYWORDS  # PostgreSQL and Redshift share keywords
)

__all__ = [
    # Core implementations
    "BaseQueryBuilder",
    "SnowflakeQueryBuilder",
    "PostgresqlQueryBuilder",
    "BigqueryQueryBuilder",
    "RedshiftQueryBuilder",
    # Constants
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
