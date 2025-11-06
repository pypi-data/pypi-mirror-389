"""
Custom exceptions for the multi-database query builder.

This module defines all custom exceptions used throughout the query builder system,
providing clear error handling and debugging information.
"""

from typing import Any, Dict, Optional


class QueryBuilderError(Exception):
    """Base exception for all query builder errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class UnsupportedDatabaseError(QueryBuilderError):
    """Raised when an unsupported database type is requested."""

    def __init__(self, database_type: str, supported_types: Optional[list] = None):
        message = f"Unsupported database type: {database_type}"
        details = {"database_type": database_type}
        if supported_types:
            details["supported_types"] = supported_types
            message += f". Supported types: {', '.join(supported_types)}"
        super().__init__(message, details)


class QueryExecutionError(QueryBuilderError):
    """Raised when a query execution fails."""

    def __init__(self, query: str, error: str, database_type: Optional[str] = None):
        message = f"Query execution failed: {error}"
        details = {
            "query": query,
            "error": error,
        }
        if database_type:
            details["database_type"] = database_type
        super().__init__(message, details)


class ValidationError(QueryBuilderError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: Any, reason: str):
        message = f"Validation failed for field '{field}': {reason}"
        details = {
            "field": field,
            "value": value,
            "reason": reason,
        }
        super().__init__(message, details)


class ConfigurationError(QueryBuilderError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, config_key: str, reason: str):
        message = f"Configuration error for '{config_key}': {reason}"
        details = {
            "config_key": config_key,
            "reason": reason,
        }
        super().__init__(message, details)


class ConnectionError(QueryBuilderError):
    """Raised when database connection fails."""

    def __init__(self, database_type: str, error: str):
        message = f"Database connection failed for {database_type}: {error}"
        details = {
            "database_type": database_type,
            "error": error,
        }
        super().__init__(message, details)


class SchemaError(QueryBuilderError):
    """Raised when schema-related operations fail."""

    def __init__(self, schema_name: str, operation: str, error: str):
        message = (
            f"Schema operation '{operation}' failed for schema '{schema_name}': {error}"
        )
        details = {
            "schema_name": schema_name,
            "operation": operation,
            "error": error,
        }
        super().__init__(message, details)


class TableError(QueryBuilderError):
    """Raised when table-related operations fail."""

    def __init__(
        self,
        table_name: str,
        operation: str,
        error: str,
        schema_name: Optional[str] = None,
    ):
        message = (
            f"Table operation '{operation}' failed for table '{table_name}': {error}"
        )
        details = {
            "table_name": table_name,
            "operation": operation,
            "error": error,
        }
        if schema_name:
            details["schema_name"] = schema_name
            message = f"Table operation '{operation}' failed for table '{schema_name}.{table_name}': {error}"
        super().__init__(message, details)


class ColumnError(QueryBuilderError):
    """Raised when column-related operations fail."""

    def __init__(
        self,
        column_name: str,
        operation: str,
        error: str,
        table_name: Optional[str] = None,
    ):
        message = (
            f"Column operation '{operation}' failed for column '{column_name}': {error}"
        )
        details = {
            "column_name": column_name,
            "operation": operation,
            "error": error,
        }
        if table_name:
            details["table_name"] = table_name
            message = f"Column operation '{operation}' failed for column '{table_name}.{column_name}': {error}"
        super().__init__(message, details)


class FunctionError(QueryBuilderError):
    """Raised when SQL function operations fail."""

    def __init__(
        self,
        function_name: str,
        error: str,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        message = f"Function '{function_name}' failed: {error}"
        details = {
            "function_name": function_name,
            "error": error,
        }
        if parameters:
            details["parameters"] = parameters
        super().__init__(message, details)
