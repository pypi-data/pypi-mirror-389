"""
Core interfaces for the multi-database query builder.

This module defines the abstract base classes and interfaces that all
database-specific implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class QueryBuilderInterface(ABC):
    """Abstract base class for all database query builders."""

    def __init__(self, database_type: str):
        self.database_type = database_type

    # Schema operations
    @abstractmethod
    def check_if_table_exists(
        self, db_session, schema_name: str, table_name: str
    ) -> bool:
        """Check if a table exists in the specified schema."""
        pass

    @abstractmethod
    def check_if_column_exists(
        self, db_session, schema_name: str, table_name: str, column_name: str
    ) -> bool:
        """Check if a column exists in the specified table."""
        pass

    @abstractmethod
    def get_schemas_like_pattern(
        self,
        db_session,
        schema_name: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Get schemas matching a pattern."""
        pass

    @abstractmethod
    def fetch_column_name(
        self, db_session, schema_name: str, table_name: str
    ) -> List[str]:
        """Fetch column names from a table."""
        pass

    @abstractmethod
    def fetch_column_name_datatype(
        self,
        db_session,
        schema_name: str,
        table_name: str,
        filter_val: str = "fivetran",
    ) -> List[Dict[str, str]]:
        """Fetch column names and data types from a table."""
        pass

    @abstractmethod
    def fetch_single_column_name_datatype(
        self, db_session, schema_name: str, table_name: str, column_name: str
    ) -> Dict[str, str]:
        """Fetch name and data type of a single column."""
        pass

    @abstractmethod
    def fetch_all_tables_in_schema(
        self,
        db_session,
        schema_name: str,
        pattern: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Fetch all tables in a schema."""
        pass

    @abstractmethod
    def fetch_all_views_in_schema(
        self, db_session, schema_name: str, pattern: Optional[str] = None
    ) -> List[str]:
        """Fetch all views in a schema."""
        pass

    @abstractmethod
    def fetch_table_type_in_schema(
        self, db_session, schema_name: str, table_name: str
    ) -> str:
        """Fetch the type (table or view) of a specified table."""
        pass

    @abstractmethod
    def get_tables_under_schema(self, db_session, schema: str) -> List[str]:
        """Get all tables under a schema."""
        pass

    # SQL function operations
    @abstractmethod
    def mode_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for mode function."""
        pass

    @abstractmethod
    def median_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for median function."""
        pass

    @abstractmethod
    def concat_function(self, column: List[str], alias: str, separator: str) -> str:
        """Generate SQL for concatenation function."""
        pass

    @abstractmethod
    def pivot_function(
        self,
        fields: Dict[str, Any],
        column_list: List[str],
        schema: str,
        table_name: str,
    ) -> str:
        """Generate SQL for pivot function."""
        pass

    @abstractmethod
    def trim_function(
        self, column: str, value: str, condition: str, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for trim function."""
        pass

    @abstractmethod
    def split_function(
        self, column: str, delimiter: str, part: int, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for split function."""
        pass

    @abstractmethod
    def timestamp_to_date_function(
        self, column: str, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for timestamp to date conversion."""
        pass

    @abstractmethod
    def substring_function(self, column: str, start: int, end: int) -> str:
        """Generate SQL for substring function."""
        pass

    @abstractmethod
    def table_rename_query(
        self, schema_name: str, old_table_name: str, new_table_name: str
    ) -> str:
        """Generate SQL for table rename."""
        pass

    @abstractmethod
    def date_diff_in_hours(
        self, start_date: str, end_date: str, table_name: str, alias: str
    ) -> str:
        """Generate SQL for date difference in hours."""
        pass

    @abstractmethod
    def date_substraction(
        self,
        date_part: str,
        start_date: str,
        end_date: str,
        alias: Optional[str] = None,
    ) -> str:
        """Generate SQL for date subtraction."""
        pass

    # Utility operations
    @abstractmethod
    def enclose_reserved_keywords(self, query: str) -> str:
        """Enclose reserved keywords in a query."""
        pass

    @abstractmethod
    def enclose_reserved_keywords_v2(self, columns_string: str) -> str:
        """Enclose reserved keywords in a column string."""
        pass

    @abstractmethod
    def handle_reserved_keywords(self, query_string: str) -> str:
        """Handle reserved keywords in a query string."""
        pass


class DatabaseConnectionInterface(ABC):
    """Abstract interface for database connections."""

    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> Any:
        """Establish database connection."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def execute_query(self, query: str) -> Any:
        """Execute a SQL query."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass


class ValidationInterface(ABC):
    """Abstract interface for input validation."""

    @abstractmethod
    def validate_database_type(self, database_type: str) -> bool:
        """Validate database type."""
        pass

    @abstractmethod
    def validate_schema_name(self, schema_name: str) -> bool:
        """Validate schema name."""
        pass

    @abstractmethod
    def validate_table_name(self, table_name: str) -> bool:
        """Validate table name."""
        pass

    @abstractmethod
    def validate_column_name(self, column_name: str) -> bool:
        """Validate column name."""
        pass

    @abstractmethod
    def validate_query(self, query: str) -> bool:
        """Validate SQL query."""
        pass
