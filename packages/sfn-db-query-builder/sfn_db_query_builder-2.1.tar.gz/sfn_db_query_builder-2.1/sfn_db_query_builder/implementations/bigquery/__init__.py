"""
BigQuery implementation for the multi-database query builder.

This module contains the BigQuery-specific implementation of the query builder interface.
"""

from .sfn_db_query_builder import BigqueryQueryBuilder

__all__ = [
    "BigqueryQueryBuilder",
]
