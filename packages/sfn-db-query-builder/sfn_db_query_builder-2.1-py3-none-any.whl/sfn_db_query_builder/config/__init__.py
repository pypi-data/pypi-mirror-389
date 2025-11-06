"""
Configuration module for the multi-database query builder.

This module contains all configuration constants, database type definitions,
and settings for the query builder system.
"""

from .constants import (
    NUMERICAL_DATA_TYPES,
    REDSHIFT_RESERVED_KEYWORDS,
    BIGQUERY_RESERVED_KEYWORDS,
    SNOWFLAKE_RESERVED_KEYWORDS,
)
from .database_types import DatabaseType
__all__ = [
    "NUMERICAL_DATA_TYPES",
    "REDSHIFT_RESERVED_KEYWORDS", 
    "BIGQUERY_RESERVED_KEYWORDS",
    "SNOWFLAKE_RESERVED_KEYWORDS",
    "DatabaseType",
]
