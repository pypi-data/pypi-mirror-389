"""
PostgreSQL implementation for the multi-database query builder.

This module contains the PostgreSQL-specific implementation of the query builder interface.
"""

from .sfn_db_query_builder import PostgresqlQueryBuilder

__all__ = [
    "PostgresqlQueryBuilder",
]
