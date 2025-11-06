"""
Core abstractions for the multi-database query builder.

This module contains the core interfaces, factory patterns, and base classes
that define the architecture of the query builder system.
"""

from .interfaces import QueryBuilderInterface
from .factory import DatabaseQueryBuilderFactory
from .exceptions import (
    QueryBuilderError,
    UnsupportedDatabaseError,
    QueryExecutionError,
    ValidationError,
    ConfigurationError,
)

__all__ = [
    "QueryBuilderInterface",
    "DatabaseQueryBuilderFactory",
    "QueryBuilderError",
    "UnsupportedDatabaseError", 
    "QueryExecutionError",
    "ValidationError",
    "ConfigurationError",
]
