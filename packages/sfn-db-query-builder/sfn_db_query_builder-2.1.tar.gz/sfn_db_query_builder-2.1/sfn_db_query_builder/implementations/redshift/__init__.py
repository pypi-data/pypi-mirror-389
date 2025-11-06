"""
Redshift implementation for the multi-database query builder.

This module contains the Redshift-specific implementation of the query builder interface.
Redshift extends PostgreSQL functionality with some specific differences.
"""

from .sfn_db_query_builder import RedshiftQueryBuilder

__all__ = [
    "RedshiftQueryBuilder",
]
