"""
Multi-Database Query Builder - Main Entry Point

This module provides the main entry point for the multi-database query builder,
using the Abstract Factory pattern to route operations to the appropriate database implementation.
"""

from typing import Any, Dict, List, Optional

from .core.factory import create_query_builder


class MultiDatabaseQueryBuilder:
    """
    Main entry point for multi-database query operations.

    This class acts as a facade that routes all operations to the appropriate
    database-specific implementation using the Abstract Factory pattern.
    """

    def __init__(self, database_type: str):
        """
        Initialize the multi-database query builder.

        Args:
            database_type: The type of database ('snowflake', 'postgresql', 'bigquery', 'redshift')
        """
        self.database_type = database_type.lower()
        self._query_builder = create_query_builder(self.database_type)

    # Schema and Table Operations
    def check_if_table_exists(
        self, db_session, schema_name: str, table_name: str
    ) -> bool:
        """Check if a table exists in the specified schema."""
        return self._query_builder.check_if_table_exists(
            db_session, schema_name, table_name
        )

    def check_if_column_exists(
        self, db_session, schema_name: str, table_name: str, column_name: str
    ) -> bool:
        """Check if a column exists in the specified table."""
        return self._query_builder.check_if_column_exists(
            db_session, schema_name, table_name, column_name
        )

    def fetch_column_name(
        self, db_session, schema_name: str, table_name: str
    ) -> List[str]:
        """Fetch all column names from a table."""
        return self._query_builder.fetch_column_name(
            db_session, schema_name, table_name
        )

    def fetch_column_name_datatype(
        self,
        db_session,
        schema_name: str,
        table_name: str,
        filter_val: str = "fivetran",
    ) -> List[Dict[str, str]]:
        """Fetch column names and their data types from a table."""
        return self._query_builder.fetch_column_name_datatype(
            db_session, schema_name, table_name, filter_val
        )

    def fetch_single_column_name_datatype(
        self, db_session, schema_name: str, table_name: str, column_name: str
    ) -> Dict[str, str]:
        """Fetch information about a single column."""
        return self._query_builder.fetch_single_column_name_datatype(
            db_session, schema_name, table_name, column_name
        )

    def get_schemas_like_pattern(
        self,
        db_session,
        schema_name: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Get schemas matching a pattern."""
        return self._query_builder.get_schemas_like_pattern(
            db_session, schema_name, source_database
        )

    def fetch_all_tables_in_schema(
        self,
        db_session,
        schema_name: str,
        pattern: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Fetch all tables in a schema."""
        return self._query_builder.fetch_all_tables_in_schema(
            db_session, schema_name, pattern, source_database
        )

    def fetch_all_views_in_schema(
        self, db_session, schema_name: str, pattern: Optional[str] = None
    ) -> List[str]:
        """Fetch all views in a schema."""
        return self._query_builder.fetch_all_views_in_schema(
            db_session, schema_name, pattern
        )

    def fetch_table_type_in_schema(
        self, db_session, schema_name: str, table_name: str
    ) -> str:
        """Fetch the type of a table (table/view)."""
        return self._query_builder.fetch_table_type_in_schema(
            db_session, schema_name, table_name
        )

    def get_tables_under_schema(self, db_session, schema: str) -> List[str]:
        """Get all tables under a schema."""
        return self._query_builder.get_tables_under_schema(db_session, schema)

    # SQL Function Generation
    def mode_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate mode function SQL."""
        return self._query_builder.mode_function(column, alias)

    def median_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate median function SQL."""
        return self._query_builder.median_function(column, alias)

    def concat_function(self, column: List[str], alias: str, separator: str) -> str:
        """Generate concatenation function SQL."""
        return self._query_builder.concat_function(column, alias, separator)

    def pivot_function(
        self,
        fields: Dict[str, Any],
        column_list: List[str],
        schema: str,
        table_name: str,
    ) -> str:
        """Generate pivot function SQL."""
        return self._query_builder.pivot_function(
            fields, column_list, schema, table_name
        )

    def trim_function(
        self, column: str, value: str, condition: str, alias: Optional[str] = None
    ) -> str:
        """Generate trim function SQL."""
        return self._query_builder.trim_function(column, value, condition, alias)

    def split_function(
        self, column: str, delimiter: str, part: int, alias: Optional[str] = None
    ) -> str:
        """Generate split function SQL."""
        return self._query_builder.split_function(column, delimiter, part, alias)

    def timestamp_to_date_function(
        self, column: str, alias: Optional[str] = None
    ) -> str:
        """Generate timestamp to date conversion SQL."""
        return self._query_builder.timestamp_to_date_function(column, alias)

    def substring_function(self, column: str, start: int, end: int) -> str:
        """Generate substring function SQL."""
        return self._query_builder.substring_function(column, start, end)

    def table_rename_query(
        self, schema_name: str, old_table_name: str, new_table_name: str
    ) -> str:
        """Generate table rename query SQL."""
        return self._query_builder.table_rename_query(
            schema_name, old_table_name, new_table_name
        )

    def date_diff_in_hours(
        self, start_date: str, end_date: str, table_name: str, alias: str
    ) -> str:
        """Generate date difference in hours SQL."""
        return self._query_builder.date_diff_in_hours(
            start_date, end_date, table_name, alias
        )

    def date_substraction(
        self,
        date_part: str,
        start_date: str,
        end_date: str,
        alias: Optional[str] = None,
    ) -> str:
        """Generate date subtraction SQL."""
        return self._query_builder.date_substraction(
            date_part, start_date, end_date, alias
        )

    # Query Processing
    def enclose_reserved_keywords(self, query: str) -> str:
        """Enclose reserved keywords in quotes."""
        return self._query_builder.enclose_reserved_keywords(query)

    def enclose_reserved_keywords_v2(self, columns_string: str) -> str:
        """Enclose reserved keywords in quotes (version 2)."""
        return self._query_builder.enclose_reserved_keywords_v2(columns_string)

    def handle_reserved_keywords(self, query_string: str) -> str:
        """Handle reserved keywords in query string."""
        return self._query_builder.handle_reserved_keywords(query_string)


# Standalone function interface for backward compatibility
def check_if_table_exists(
    data_store: str, db_session, schema_name: str, table_name: str
) -> bool:
    """Check if a table exists in the specified schema."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.check_if_table_exists(db_session, schema_name, table_name)


def check_if_column_exists(
    data_store: str, db_session, schema_name: str, table_name: str, column_name: str
) -> bool:
    """Check if a column exists in the specified table."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.check_if_column_exists(
        db_session, schema_name, table_name, column_name
    )


def fetch_column_name(
    data_store: str, db_session, schema_name: str, table_name: str
) -> List[str]:
    """Fetch all column names from a table."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.fetch_column_name(db_session, schema_name, table_name)


def fetch_column_name_datatype(
    data_store: str,
    db_session,
    schema_name: str,
    table_name: str,
    filter_val: str = "fivetran",
) -> List[Dict[str, str]]:
    """Fetch column names and their data types from a table."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.fetch_column_name_datatype(
        db_session, schema_name, table_name, filter_val
    )


def fetch_single_column_name_datatype(
    data_store: str, db_session, schema_name: str, table_name: str, column_name: str
) -> Dict[str, str]:
    """Fetch information about a single column."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.fetch_single_column_name_datatype(
        db_session, schema_name, table_name, column_name
    )


def get_schemas_like_pattern(
    data_store: str,
    db_session,
    schema_name: Optional[str] = None,
    source_database: Optional[str] = None,
) -> List[str]:
    """Get schemas matching a pattern."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.get_schemas_like_pattern(db_session, schema_name, source_database)


def fetch_all_tables_in_schema(
    data_store: str,
    db_session,
    schema_name: str,
    pattern: Optional[str] = None,
    source_database: Optional[str] = None,
) -> List[str]:
    """Fetch all tables in a schema."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.fetch_all_tables_in_schema(
        db_session, schema_name, pattern, source_database
    )


def fetch_all_views_in_schema(
    data_store: str, db_session, schema_name: str, pattern: Optional[str] = None
) -> List[str]:
    """Fetch all views in a schema."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.fetch_all_views_in_schema(db_session, schema_name, pattern)


def fetch_table_type_in_schema(
    data_store: str, db_session, schema_name: str, table_name: str
) -> str:
    """Fetch the type of a table (table/view)."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.fetch_table_type_in_schema(db_session, schema_name, table_name)


def get_tables_under_schema(data_store: str, db_session, schema: str) -> List[str]:
    """Get all tables under a schema."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.get_tables_under_schema(db_session, schema)


def mode_function(data_store: str, column: str, alias: Optional[str] = None) -> str:
    """Generate mode function SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.mode_function(column, alias)


def median_function(data_store: str, column: str, alias: Optional[str] = None) -> str:
    """Generate median function SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.median_function(column, alias)


def concat_function(
    data_store: str, column: List[str], alias: str, separator: str
) -> str:
    """Generate concatenation function SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.concat_function(column, alias, separator)


def pivot_function(
    data_store: str,
    fields: Dict[str, Any],
    column_list: List[str],
    schema: str,
    table_name: str,
) -> str:
    """Generate pivot function SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.pivot_function(fields, column_list, schema, table_name)


def trim_function(
    data_store: str,
    column: str,
    value: str,
    condition: str,
    alias: Optional[str] = None,
) -> str:
    """Generate trim function SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.trim_function(column, value, condition, alias)


def split_function(
    data_store: str, column: str, delimiter: str, part: int, alias: Optional[str] = None
) -> str:
    """Generate split function SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.split_function(column, delimiter, part, alias)


def timestamp_to_date_function(
    data_store: str, column: str, alias: Optional[str] = None
) -> str:
    """Generate timestamp to date conversion SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.timestamp_to_date_function(column, alias)


def substring_function(data_store: str, column: str, start: int, end: int) -> str:
    """Generate substring function SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.substring_function(column, start, end)


def table_rename_query(
    data_store: str, schema_name: str, old_table_name: str, new_table_name: str
) -> str:
    """Generate table rename query SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.table_rename_query(schema_name, old_table_name, new_table_name)


def date_diff_in_hours(
    data_store: str, start_date: str, end_date: str, table_name: str, alias: str
) -> str:
    """Generate date difference in hours SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.date_diff_in_hours(start_date, end_date, table_name, alias)


def date_substraction(
    data_store: str,
    date_part: str,
    start_date: str,
    end_date: str,
    alias: Optional[str] = None,
) -> str:
    """Generate date subtraction SQL."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.date_substraction(date_part, start_date, end_date, alias)


def enclose_reserved_keywords(data_store: str, query: str) -> str:
    """Enclose reserved keywords in quotes."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.enclose_reserved_keywords(query)


def enclose_reserved_keywords_v2(data_store: str, columns_string: str) -> str:
    """Enclose reserved keywords in quotes (version 2)."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.enclose_reserved_keywords_v2(columns_string)


def handle_reserved_keywords(data_store: str, query_string: str) -> str:
    """Handle reserved keywords in query string."""
    builder = MultiDatabaseQueryBuilder(data_store)
    return builder.handle_reserved_keywords(query_string)
