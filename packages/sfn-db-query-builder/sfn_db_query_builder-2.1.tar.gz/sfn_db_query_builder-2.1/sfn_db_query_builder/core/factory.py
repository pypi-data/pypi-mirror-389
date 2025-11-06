"""
Abstract Factory pattern implementation for database query builders.

This module implements the Abstract Factory pattern to create database-specific
query builders based on the database type.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from ..config.database_types import DatabaseType
from .exceptions import UnsupportedDatabaseError
from .interfaces import QueryBuilderInterface


class DatabaseQueryBuilderFactory(ABC):
    """Abstract factory for creating database query builders."""

    @abstractmethod
    def create_query_builder(self) -> QueryBuilderInterface:
        """Create a query builder instance."""
        pass


class SnowflakeQueryBuilderFactory(DatabaseQueryBuilderFactory):
    """Factory for creating Snowflake query builders."""

    def create_query_builder(self) -> QueryBuilderInterface:
        """Create a Snowflake query builder instance."""
        from ..implementations.snowflake.sfn_db_query_builder import (
            SnowflakeQueryBuilder,
        )

        return SnowflakeQueryBuilder(DatabaseType.SNOWFLAKE.value)


class PostgresqlQueryBuilderFactory(DatabaseQueryBuilderFactory):
    """Factory for creating PostgreSQL query builders."""

    def create_query_builder(self) -> QueryBuilderInterface:
        """Create a PostgreSQL query builder instance."""
        from ..implementations.postgresql.sfn_db_query_builder import (
            PostgresqlQueryBuilder,
        )

        return PostgresqlQueryBuilder(DatabaseType.POSTGRESQL.value)


class BigqueryQueryBuilderFactory(DatabaseQueryBuilderFactory):
    """Factory for creating BigQuery query builders."""

    def create_query_builder(self) -> QueryBuilderInterface:
        """Create a BigQuery query builder instance."""
        from ..implementations.bigquery.sfn_db_query_builder import BigqueryQueryBuilder

        return BigqueryQueryBuilder(DatabaseType.BIGQUERY.value)


class RedshiftQueryBuilderFactory(DatabaseQueryBuilderFactory):
    """Factory for creating Redshift query builders."""

    def create_query_builder(self) -> QueryBuilderInterface:
        """Create a Redshift query builder instance."""
        from ..implementations.redshift.sfn_db_query_builder import RedshiftQueryBuilder

        return RedshiftQueryBuilder(DatabaseType.REDSHIFT.value)


class QueryBuilderFactoryRegistry:
    """Registry for managing database query builder factories."""

    def __init__(self):
        self._factories: Dict[str, Type[DatabaseQueryBuilderFactory]] = {
            DatabaseType.SNOWFLAKE.value: SnowflakeQueryBuilderFactory,
            DatabaseType.POSTGRESQL.value: PostgresqlQueryBuilderFactory,
            DatabaseType.BIGQUERY.value: BigqueryQueryBuilderFactory,
            DatabaseType.REDSHIFT.value: RedshiftQueryBuilderFactory,
        }

    def register_factory(
        self, database_type: str, factory_class: Type[DatabaseQueryBuilderFactory]
    ) -> None:
        """Register a new factory for a database type."""
        self._factories[database_type] = factory_class

    def get_factory(self, database_type: str) -> DatabaseQueryBuilderFactory:
        """Get a factory for the specified database type."""
        if database_type not in self._factories:
            supported_types = list(self._factories.keys())
            raise UnsupportedDatabaseError(database_type, supported_types)

        factory_class = self._factories[database_type]
        return factory_class()

    def get_supported_database_types(self) -> list:
        """Get list of supported database types."""
        return list(self._factories.keys())

    def is_supported(self, database_type: str) -> bool:
        """Check if a database type is supported."""
        return database_type in self._factories


# Global factory registry instance
_factory_registry: Optional[QueryBuilderFactoryRegistry] = None


def get_factory_registry() -> QueryBuilderFactoryRegistry:
    """Get the global factory registry instance."""
    global _factory_registry
    if _factory_registry is None:
        _factory_registry = QueryBuilderFactoryRegistry()
    return _factory_registry


def create_query_builder(database_type: str) -> QueryBuilderInterface:
    """Create a query builder for the specified database type.

    Args:
        database_type: The type of database (snowflake, postgresql, bigquery, redshift)

    Returns:
        QueryBuilderInterface: A database-specific query builder instance

    Raises:
        UnsupportedDatabaseError: If the database type is not supported
    """
    registry = get_factory_registry()
    factory = registry.get_factory(database_type)
    return factory.create_query_builder()


def get_supported_database_types() -> list:
    """Get list of all supported database types."""
    registry = get_factory_registry()
    return registry.get_supported_database_types()


def is_database_supported(database_type: str) -> bool:
    """Check if a database type is supported."""
    registry = get_factory_registry()
    return registry.is_supported(database_type)


# Legacy function for backward compatibility
def get_data_object(data_store: str) -> QueryBuilderInterface:
    """Legacy function for backward compatibility.

    This function maintains compatibility with the old DatabaseObjectHandler.get_data_object method.

    Args:
        data_store: The database type

    Returns:
        QueryBuilderInterface: A database-specific query builder instance

    Raises:
        UnsupportedDatabaseError: If the database type is not supported
    """
    return create_query_builder(data_store)
