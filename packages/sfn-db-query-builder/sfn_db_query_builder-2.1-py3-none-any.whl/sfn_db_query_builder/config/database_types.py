"""
Database type definitions and constants.

This module defines the supported database types and provides
utility functions for database type validation and management.
"""

from enum import Enum
from typing import Any, Dict, List


class DatabaseType(Enum):
    """Enumeration of supported database types."""

    SNOWFLAKE = "snowflake"
    POSTGRESQL = "postgresql"
    BIGQUERY = "bigquery"
    REDSHIFT = "redshift"

    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of all supported database types."""
        return [db_type.value for db_type in cls]

    @classmethod
    def is_supported(cls, database_type: str) -> bool:
        """Check if a database type is supported."""
        return database_type.lower() in cls.get_supported_types()

    @classmethod
    def validate(cls, database_type: str) -> str:
        """Validate and normalize database type."""
        if not cls.is_supported(database_type):
            raise ValueError(f"Unsupported database type: {database_type}")
        return database_type.lower()


# Database type aliases for backward compatibility
SNOWFLAKE = DatabaseType.SNOWFLAKE.value
POSTGRESQL = DatabaseType.POSTGRESQL.value
BIGQUERY = DatabaseType.BIGQUERY.value
REDSHIFT = DatabaseType.REDSHIFT.value


# Database-specific configuration
DATABASE_CONFIG: Dict[str, Dict[str, Any]] = {
    DatabaseType.SNOWFLAKE.value: {
        "case_sensitive": False,
        "identifier_quote": '"',
        "supports_views": True,
        "supports_pivot": True,
        "supports_mode": True,
        "supports_median": True,
    },
    DatabaseType.POSTGRESQL.value: {
        "case_sensitive": True,
        "identifier_quote": '"',
        "supports_views": True,
        "supports_pivot": True,
        "supports_mode": True,
        "supports_median": False,
    },
    DatabaseType.BIGQUERY.value: {
        "case_sensitive": False,
        "identifier_quote": "`",
        "supports_views": True,
        "supports_pivot": False,
        "supports_mode": False,
        "supports_median": False,
    },
    DatabaseType.REDSHIFT.value: {
        "case_sensitive": True,
        "identifier_quote": '"',
        "supports_views": True,
        "supports_pivot": True,
        "supports_mode": True,
        "supports_median": False,
    },
}


def get_database_config(database_type: str) -> Dict[str, Any]:
    """Get configuration for a specific database type."""
    normalized_type = DatabaseType.validate(database_type)
    return DATABASE_CONFIG.get(normalized_type, {})


def get_supported_database_types() -> List[str]:
    """Get list of all supported database types."""
    return DatabaseType.get_supported_types()


def is_feature_supported(database_type: str, feature: str) -> bool:
    """Check if a specific feature is supported by the database type."""
    config = get_database_config(database_type)
    return config.get(f"supports_{feature}", False)


def supports_feature(database_type: str, feature: str) -> bool:
    """Check if a specific feature is supported by the database type."""
    return is_feature_supported(database_type, feature)
