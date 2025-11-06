"""
Base implementation class for database query builders.

This module provides a base implementation class that contains common functionality
and helper methods that can be shared across all database-specific implementations.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from ..config.constants import NUMERICAL_DATA_TYPES
from ..config.database_types import get_database_config
from ..core.exceptions import QueryExecutionError, ValidationError
from ..core.interfaces import QueryBuilderInterface


class BaseQueryBuilder(QueryBuilderInterface):
    """Base implementation class for database query builders."""

    def __init__(self, database_type: str):
        super().__init__(database_type)
        self.config = get_database_config(database_type)
        self.logger = logging.getLogger(f"{__name__}.{database_type}")

    def _validate_input(self, **kwargs) -> None:
        """Validate input parameters."""
        for key, value in kwargs.items():
            if value is None:
                raise ValidationError(key, value, "Value cannot be None")
            if isinstance(value, str) and not value.strip():
                raise ValidationError(key, value, "String value cannot be empty")

    def _execute_query(self, db_session, query: str) -> Any:
        """Execute a query with error handling."""
        try:
            self.logger.debug(f"Executing query: {query}")
            result = db_session.execute(text(query))
            return result
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def _filter_columns(
        self, columns: List[Dict[str, str]], filter_val: str = "fivetran"
    ) -> List[Dict[str, str]]:
        """Filter columns based on filter value."""
        if not filter_val:
            return columns

        filtered_columns = []
        for column in columns:
            column_name = column.get("column_name", "").lower()
            if filter_val.lower() not in column_name:
                filtered_columns.append(column)

        return filtered_columns

    def _normalize_data_type(self, data_type: str) -> str:
        """Normalize data type by removing precision and scale information."""
        # Remove precision and scale (e.g., varchar(255) -> varchar)
        normalized = re.sub(r"\([^)]*\)", "", data_type)
        # Remove underscore suffixes (e.g., varchar_255 -> varchar)
        normalized = normalized.split("_")[0]
        return normalized.lower()

    def _is_numerical_type(self, data_type: str) -> bool:
        """Check if a data type is numerical."""
        normalized_type = self._normalize_data_type(data_type)
        return normalized_type in NUMERICAL_DATA_TYPES

    def _quote_identifier(self, identifier: str) -> str:
        """Quote an identifier based on database configuration."""
        quote_char = self.config.get("identifier_quote", '"')
        return f"{quote_char}{identifier}{quote_char}"

    def _build_where_clause(self, conditions: Dict[str, Any]) -> str:
        """Build a WHERE clause from conditions."""
        if not conditions:
            return ""

        where_parts = []
        for column, value in conditions.items():
            if isinstance(value, str):
                where_parts.append(f"{column} = '{value}'")
            else:
                where_parts.append(f"{column} = {value}")

        return "WHERE " + " AND ".join(where_parts)

    def _build_order_clause(self, order_by: List[str], ascending: bool = True) -> str:
        """Build an ORDER BY clause."""
        if not order_by:
            return ""

        direction = "ASC" if ascending else "DESC"
        return f"ORDER BY {', '.join(order_by)} {direction}"

    def _build_limit_clause(self, limit: Optional[int] = None) -> str:
        """Build a LIMIT clause."""
        if limit is None:
            return ""
        return f"LIMIT {limit}"

    def _sanitize_identifier(self, identifier: str) -> str:
        """Sanitize an identifier to prevent SQL injection."""
        # Remove any characters that could be used for SQL injection
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "", identifier)
        return sanitized

    def _validate_schema_name(self, schema_name: str) -> None:
        """Validate schema name."""
        if not schema_name or not schema_name.strip():
            raise ValidationError(
                "schema_name", schema_name, "Schema name cannot be empty"
            )

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", schema_name):
            raise ValidationError(
                "schema_name", schema_name, "Schema name contains invalid characters"
            )

    def _validate_table_name(self, table_name: str) -> None:
        """Validate table name."""
        if not table_name or not table_name.strip():
            raise ValidationError(
                "table_name", table_name, "Table name cannot be empty"
            )

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            raise ValidationError(
                "table_name", table_name, "Table name contains invalid characters"
            )

    def _validate_column_name(self, column_name: str) -> None:
        """Validate column name."""
        if not column_name or not column_name.strip():
            raise ValidationError(
                "column_name", column_name, "Column name cannot be empty"
            )

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column_name):
            raise ValidationError(
                "column_name", column_name, "Column name contains invalid characters"
            )

    def _log_performance(self, operation: str, duration: float) -> None:
        """Log performance metrics for an operation."""
        if duration > 5.0:  # Log slow operations
            self.logger.warning(
                f"Slow operation '{operation}' took {duration:.2f} seconds"
            )
        else:
            self.logger.debug(
                f"Operation '{operation}' completed in {duration:.2f} seconds"
            )

    def _format_error_message(self, operation: str, error: str, **context) -> str:
        """Format error message with context."""
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        return f"{operation} failed: {error} (Context: {context_str})"

    # Abstract methods that must be implemented by subclasses
    # These are the core methods that are database-specific

    def check_if_table_exists(
        self, db_session, schema_name: str, table_name: str
    ) -> bool:
        """Check if a table exists in the specified schema."""
        raise NotImplementedError("Subclasses must implement check_if_table_exists")

    def check_if_column_exists(
        self, db_session, schema_name: str, table_name: str, column_name: str
    ) -> bool:
        """Check if a column exists in the specified table."""
        raise NotImplementedError("Subclasses must implement check_if_column_exists")

    def get_schemas_like_pattern(
        self,
        db_session,
        schema_name: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Get schemas matching a pattern."""
        raise NotImplementedError("Subclasses must implement get_schemas_like_pattern")

    def fetch_column_name(
        self, db_session, schema_name: str, table_name: str
    ) -> List[str]:
        """Fetch column names from a table."""
        raise NotImplementedError("Subclasses must implement fetch_column_name")

    def fetch_column_name_datatype(
        self,
        db_session,
        schema_name: str,
        table_name: str,
        filter_val: str = "fivetran",
    ) -> List[Dict[str, str]]:
        """Fetch column names and data types from a table."""
        raise NotImplementedError(
            "Subclasses must implement fetch_column_name_datatype"
        )

    def fetch_single_column_name_datatype(
        self, db_session, schema_name: str, table_name: str, column_name: str
    ) -> Dict[str, str]:
        """Fetch name and data type of a single column."""
        raise NotImplementedError(
            "Subclasses must implement fetch_single_column_name_datatype"
        )

    def fetch_all_tables_in_schema(
        self,
        db_session,
        schema_name: str,
        pattern: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Fetch all tables in a schema."""
        raise NotImplementedError(
            "Subclasses must implement fetch_all_tables_in_schema"
        )

    def fetch_all_views_in_schema(
        self, db_session, schema_name: str, pattern: Optional[str] = None
    ) -> List[str]:
        """Fetch all views in a schema."""
        raise NotImplementedError("Subclasses must implement fetch_all_views_in_schema")

    def fetch_table_type_in_schema(
        self, db_session, schema_name: str, table_name: str
    ) -> str:
        """Fetch the type (table or view) of a specified table."""
        raise NotImplementedError(
            "Subclasses must implement fetch_table_type_in_schema"
        )

    def get_tables_under_schema(self, db_session, schema: str) -> List[str]:
        """Get all tables under a schema."""
        raise NotImplementedError("Subclasses must implement get_tables_under_schema")

    def mode_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for mode function."""
        raise NotImplementedError("Subclasses must implement mode_function")

    def median_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for median function."""
        raise NotImplementedError("Subclasses must implement median_function")

    def concat_function(self, column: List[str], alias: str, separator: str) -> str:
        """Generate SQL for concatenation function."""
        raise NotImplementedError("Subclasses must implement concat_function")

    def pivot_function(
        self,
        fields: Dict[str, Any],
        column_list: List[str],
        schema: str,
        table_name: str,
    ) -> str:
        """Generate SQL for pivot function."""
        raise NotImplementedError("Subclasses must implement pivot_function")

    def trim_function(
        self, column: str, value: str, condition: str, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for trim function."""
        raise NotImplementedError("Subclasses must implement trim_function")

    def split_function(
        self, column: str, delimiter: str, part: int, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for split function."""
        raise NotImplementedError("Subclasses must implement split_function")

    def timestamp_to_date_function(
        self, column: str, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for timestamp to date conversion."""
        raise NotImplementedError(
            "Subclasses must implement timestamp_to_date_function"
        )

    def substring_function(self, column: str, start: int, end: int) -> str:
        """Generate SQL for substring function."""
        raise NotImplementedError("Subclasses must implement substring_function")

    def table_rename_query(
        self, schema_name: str, old_table_name: str, new_table_name: str
    ) -> str:
        """Generate SQL for table rename."""
        raise NotImplementedError("Subclasses must implement table_rename_query")

    def date_diff_in_hours(
        self, start_date: str, end_date: str, table_name: str, alias: str
    ) -> str:
        """Generate SQL for date difference in hours."""
        raise NotImplementedError("Subclasses must implement date_diff_in_hours")

    def date_substraction(
        self,
        date_part: str,
        start_date: str,
        end_date: str,
        alias: Optional[str] = None,
    ) -> str:
        """Generate SQL for date subtraction."""
        raise NotImplementedError("Subclasses must implement date_substraction")

    def enclose_reserved_keywords(self, query: str) -> str:
        """Enclose reserved keywords in a query."""
        raise NotImplementedError("Subclasses must implement enclose_reserved_keywords")

    def enclose_reserved_keywords_v2(self, columns_string: str) -> str:
        """Enclose reserved keywords in a column string."""
        raise NotImplementedError(
            "Subclasses must implement enclose_reserved_keywords_v2"
        )

    def handle_reserved_keywords(self, query_string: str) -> str:
        """Handle reserved keywords in a query string."""
        raise NotImplementedError("Subclasses must implement handle_reserved_keywords")
