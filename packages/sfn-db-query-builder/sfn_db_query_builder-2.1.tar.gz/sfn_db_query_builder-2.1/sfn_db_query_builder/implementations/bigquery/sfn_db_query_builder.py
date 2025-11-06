"""
BigQuery query builder implementation.

This module provides the BigQuery-specific implementation of the query builder interface,
including all database-specific SQL generation and query execution logic.
"""

import re
from typing import Any, Dict, List, Optional

from ...config.constants import BIGQUERY_RESERVED_KEYWORDS
from ...core.exceptions import QueryExecutionError
from ..base import BaseQueryBuilder


class BigqueryQueryBuilder(BaseQueryBuilder):
    """BigQuery-specific query builder implementation."""

    def __init__(self, database_type: str):
        super().__init__(database_type)

    def check_if_table_exists(
        self, db_session, schema_name: str, table_name: str
    ) -> bool:
        """Check if a table exists in the specified schema."""
        self._validate_schema_name(schema_name)
        self._validate_table_name(table_name)

        try:
            query = f"SELECT 1 FROM {schema_name}.INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}'"
            self.logger.debug(f"Checking table existence: {query}")
            result = self._execute_query(db_session, query).fetchone()

            if not result:
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error checking table existence: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def check_if_column_exists(
        self, db_session, schema_name: str, table_name: str, column_name: str
    ) -> bool:
        """Check if a column exists in the specified table."""
        self._validate_schema_name(schema_name)
        self._validate_table_name(table_name)
        self._validate_column_name(column_name)

        try:
            query = (
                f"SELECT 1 FROM `{schema_name}.INFORMATION_SCHEMA.COLUMNS` "
                f"WHERE table_name = '{table_name}' AND table_schema = '{schema_name}' AND column_name = '{column_name}'"
            )
            self.logger.debug(f"Checking column existence: {query}")
            result = self._execute_query(db_session, query).fetchone()

            if not result:
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error checking column existence: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def get_schemas_like_pattern(
        self,
        db_session,
        schema_name: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Get schemas matching a pattern."""
        try:
            schema_query = (
                "SELECT lower(schema_name) FROM INFORMATION_SCHEMA.SCHEMATA "
            )
            condition = (
                f"WHERE schema_name LIKE lower('%{schema_name}%')"
                if schema_name
                else ""
            )
            schema_query = schema_query + condition

            self.logger.debug(f"Getting schemas: {schema_query}")
            result = self._execute_query(db_session, schema_query).fetchall()

            schemas = []
            for schema in result:
                schemas.append(schema[0])
            return schemas
        except Exception as e:
            self.logger.error(f"Error getting schemas: {e}")
            raise QueryExecutionError(schema_query, str(e), self.database_type)

    def fetch_column_name(
        self, db_session, schema_name: str, table_name: str
    ) -> List[str]:
        """Fetch column names from a table."""
        self._validate_schema_name(schema_name)
        self._validate_table_name(table_name)

        try:
            query = (
                f"SELECT column_name, data_type FROM `{schema_name}.INFORMATION_SCHEMA.COLUMNS` "
                f"WHERE table_name = '{table_name}' AND table_schema = '{schema_name}' ORDER BY ordinal_position"
            )
            self.logger.debug(f"Fetching column names: {query}")
            result = self._execute_query(db_session, query).fetchall()

            fields = []
            if result and len(result) > 0:
                for column in result:
                    fields.append(column[0])
                return fields
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error fetching column names: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def fetch_column_name_datatype(
        self,
        db_session,
        schema_name: str,
        table_name: str,
        filter_val: str = "fivetran",
    ) -> List[Dict[str, str]]:
        """Fetch column names and data types from a table."""
        self._validate_schema_name(schema_name)
        self._validate_table_name(table_name)

        try:
            query = (
                f"SELECT column_name, data_type FROM `{schema_name}.INFORMATION_SCHEMA.COLUMNS` "
                f"WHERE table_name = '{table_name}' AND table_schema = '{schema_name}' ORDER BY ordinal_position"
            )
            self.logger.debug(f"Fetching column names and types: {query}")
            result = self._execute_query(db_session, query).fetchall()

            fields = []
            if result and len(result) > 0:
                for column in result:
                    temp = {
                        "column_name": column[0],
                        "data_type": self._normalize_data_type(column[1]),
                    }
                    fields.append(temp)
                return fields
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error fetching column names and types: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def fetch_single_column_name_datatype(
        self, db_session, schema_name: str, table_name: str, column_name: str
    ) -> Dict[str, str]:
        """Fetch name and data type of a single column."""
        self._validate_schema_name(schema_name)
        self._validate_table_name(table_name)
        self._validate_column_name(column_name)

        try:
            query = (
                f"SELECT column_name, data_type FROM `{schema_name}.INFORMATION_SCHEMA.COLUMNS` "
                f"WHERE table_name = '{table_name}' AND table_schema = '{schema_name}' AND column_name = '{column_name}'"
            )
            self.logger.debug(f"Fetching single column info: {query}")
            result = self._execute_query(db_session, query).fetchone()

            fields = {}
            if result and len(result) > 0:
                fields = {
                    "column_name": result[0],
                    "data_type": self._normalize_data_type(result[1]),
                }
                return fields
            return fields
        except Exception as e:
            self.logger.error(f"Error fetching single column info: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def fetch_all_tables_in_schema(
        self,
        db_session,
        schema_name: str,
        pattern: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Fetch all tables in a schema."""
        self._validate_schema_name(schema_name)

        try:
            query = "SELECT table_name from INFORMATION_SCHEMA.TABLES "
            condition = f"and table_name like '%{pattern}'" if pattern else ""
            query = query + condition

            self.logger.debug(f"Fetching tables in schema: {query}")
            result = self._execute_query(db_session, query).fetchall()

            tables_list = []
            if result and len(result) > 0:
                tables_list.append(result[0])
            return tables_list
        except Exception as e:
            self.logger.error(f"Error fetching tables in schema: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def fetch_all_views_in_schema(
        self, db_session, schema_name: str, pattern: Optional[str] = None
    ) -> List[str]:
        """Fetch all views in a schema."""
        # BigQuery views implementation - TODO: Complete implementation
        self.logger.warning("BigQuery views implementation not yet complete")
        return []

    def fetch_table_type_in_schema(
        self, db_session, schema_name: str, table_name: str
    ) -> str:
        """Fetch the type (table or view) of a specified table."""
        # BigQuery table type implementation - TODO: Complete implementation
        self.logger.warning("BigQuery table type implementation not yet complete")
        return "TABLE"

    def get_tables_under_schema(self, db_session, schema: str) -> List[str]:
        """Get all tables under a schema."""
        self._validate_schema_name(schema)

        try:
            query = (
                f"SELECT distinct table_name FROM `{schema}.INFORMATION_SCHEMA.TABLES` "
                f"WHERE table_schema = '{schema}' and table_type = 'BASE TABLE';"
            )
            self.logger.debug(f"Getting tables under schema: {query}")
            result = self._execute_query(db_session, query).fetchall()

            tables = []
            for res in result:
                tables.append(res.table_name)
            return tables
        except Exception as e:
            self.logger.error(f"Error getting tables under schema: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    # SQL Function Operations

    def mode_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for mode function."""
        # BigQuery doesn't have a built-in mode function
        return ""

    def median_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for median function."""
        # BigQuery doesn't have a built-in median function
        return ""

    def concat_function(self, column: List[str], alias: str, separator: str) -> str:
        """Generate SQL for concatenation function."""
        # BigQuery uses CONCAT function
        return f" CONCAT({', '.join(column)}) AS {alias} "

    def pivot_function(
        self,
        fields: Dict[str, Any],
        column_list: List[str],
        schema: str,
        table_name: str,
    ) -> str:
        """Generate SQL for pivot function."""
        # BigQuery pivot implementation - TODO: Complete implementation
        self.logger.warning("BigQuery pivot implementation not yet complete")
        return ""

    def trim_function(
        self, column: str, value: str, condition: str, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for trim function."""
        # BigQuery trim implementation - TODO: Complete implementation
        self.logger.warning("BigQuery trim implementation not yet complete")
        return ""

    def split_function(
        self, column: str, delimiter: str, part: int, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for split function."""
        # BigQuery split implementation - TODO: Complete implementation
        self.logger.warning("BigQuery split implementation not yet complete")
        return ""

    def timestamp_to_date_function(
        self, column: str, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for timestamp to date conversion."""
        # BigQuery timestamp to date implementation - TODO: Complete implementation
        self.logger.warning(
            "BigQuery timestamp to date implementation not yet complete"
        )
        return ""

    def substring_function(self, column: str, start: int, end: int) -> str:
        """Generate SQL for substring function."""
        # BigQuery substring implementation - TODO: Complete implementation
        self.logger.warning("BigQuery substring implementation not yet complete")
        return ""

    def table_rename_query(
        self, schema_name: str, old_table_name: str, new_table_name: str
    ) -> str:
        """Generate SQL for table rename."""
        return f"ALTER TABLE {schema_name}.{old_table_name} RENAME TO {new_table_name}"

    def date_diff_in_hours(
        self, start_date: str, end_date: str, table_name: str, alias: str
    ) -> str:
        """Generate SQL for date difference in hours."""
        query = f"""SELECT *, 
        EXTRACT(EPOCH FROM CAST({end_date} AS TIMESTAMP) - CAST({start_date} AS TIMESTAMP)) / 3600 AS {alias}
        FROM {table_name}"""
        return query

    def date_substraction(
        self,
        date_part: str,
        start_date: str,
        end_date: str,
        alias: Optional[str] = None,
    ) -> str:
        """Generate SQL for date subtraction."""
        query = f"DATEDIFF(HOUR, {start_date}, {end_date})"
        if alias:
            query += f" as {alias}"
        return query

    # Utility Operations

    def enclose_reserved_keywords(self, query: str) -> str:
        """Enclose reserved keywords in a query."""
        try:
            # Regular expression pattern to identify reserved keywords used as column names
            pattern = r"(?i)SELECT\s+(?P<columns>.+?)\s+FROM"

            # Define a function to replace reserved keywords with double-quoted versions
            def replace_keywords(match):
                columns = match.group("columns")
                for keyword in BIGQUERY_RESERVED_KEYWORDS:
                    columns = re.sub(
                        rf"\b({keyword})\b",
                        rf'"{keyword}"',
                        columns,
                        flags=re.IGNORECASE,
                    )
                return f"SELECT {columns} FROM"

            # Use re.sub() to enclose reserved keywords with double quotes without changing their case
            return re.sub(pattern, replace_keywords, query)
        except Exception as e:
            self.logger.error(f"Error enclosing reserved keywords: {e}")
            return query

    def enclose_reserved_keywords_v2(self, columns_string: str) -> str:
        """Enclose reserved keywords in a column string."""
        try:
            columns = [col.strip() for col in columns_string.split(",")]
            enclosed_columns = [
                '"{}"'.format(col) if col in BIGQUERY_RESERVED_KEYWORDS else col
                for col in columns
            ]
            return ", ".join(enclosed_columns)
        except Exception as e:
            self.logger.error(f"Error enclosing reserved keywords v2: {e}")
            return columns_string

    def handle_reserved_keywords(self, query_string: str) -> str:
        """Handle reserved keywords in a query string."""
        # BigQuery reserved keyword handling - TODO: Complete implementation
        return query_string
