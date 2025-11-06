"""
PostgreSQL query builder implementation.

This module provides the PostgreSQL-specific implementation of the query builder interface,
including all database-specific SQL generation and query execution logic.
"""

import re
import time
from typing import Any, Dict, List, Optional

from ...config.constants import NUMERICAL_DATA_TYPES, REDSHIFT_RESERVED_KEYWORDS
from ...core.exceptions import QueryExecutionError
from ..base import BaseQueryBuilder


class PostgresqlQueryBuilder(BaseQueryBuilder):
    """PostgreSQL-specific query builder implementation."""

    def __init__(self, database_type: str):
        super().__init__(database_type)

    def check_if_table_exists(
        self, db_session, schema_name: str, table_name: str
    ) -> bool:
        """Check if a table exists in the specified schema."""
        self._validate_schema_name(schema_name)
        self._validate_table_name(table_name)

        try:
            query = (
                f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE table_name = '{table_name}' "
                f"AND table_schema = '{schema_name}'"
            )
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
                f"SELECT a.attname as column_name FROM "
                f"pg_attribute a JOIN pg_class t on a.attrelid = t.oid JOIN pg_namespace s on t.relnamespace = s.oid "
                f"WHERE a.attname = '{column_name}' and a.attnum > 0 AND NOT a.attisdropped AND t.relname = '{table_name}' AND s.nspname = '{schema_name}' "
                f"ORDER BY a.attnum;"
            )
            self.logger.debug(f"Checking column existence: {query}")
            result = self._execute_query(db_session, query).fetchone()

            if result:
                return True
            return False
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
            schema_query = "SELECT nspname FROM pg_namespace "
            condition = f"WHERE nspname ILIKE '%{schema_name}%'" if schema_name else ""
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
                f"SELECT a.attname as column_name FROM "
                f"pg_attribute a JOIN pg_class t on a.attrelid = t.oid JOIN pg_namespace s on t.relnamespace = s.oid "
                f"WHERE a.attnum > 0 AND NOT a.attisdropped AND t.relname = '{table_name}' AND s.nspname = '{schema_name}' "
                f"ORDER BY a.attnum;"
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
                f"SELECT a.attname as column_name, pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type FROM "
                f"pg_attribute a JOIN pg_class t on a.attrelid = t.oid JOIN pg_namespace s on t.relnamespace = s.oid "
                f"WHERE a.attnum > 0 AND NOT a.attisdropped AND t.relname = '{table_name}' AND s.nspname = '{schema_name}' "
                f"ORDER BY a.attnum;"
            )
            self.logger.debug(f"Fetching column names and types: {query}")
            result = self._execute_query(db_session, query).fetchall()

            fields = []
            if result and len(result) > 0:
                for column in result:
                    if filter_val in column[0].lower():
                        continue
                    else:
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
                f"SELECT a.attname as column_name, pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type FROM "
                f"pg_attribute a JOIN pg_class t on a.attrelid = t.oid JOIN pg_namespace s on t.relnamespace = s.oid "
                f"WHERE a.attnum > 0 AND NOT a.attisdropped AND t.relname = '{table_name}' AND s.nspname = '{schema_name}' "
                f"AND a.attname = '{column_name}' ORDER BY a.attnum;"
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
            query = f"SELECT table_name from INFORMATION_SCHEMA.TABLES WHERE table_schema='{schema_name}' "
            condition = f"and table_name like '%{pattern}'" if pattern else ""
            query = query + condition

            self.logger.debug(f"Fetching tables in schema: {query}")
            result = self._execute_query(db_session, query).fetchall()

            tables_list = []
            if result and len(result) > 0:
                for res in result:
                    tables_list.append(res[0])
            return tables_list
        except Exception as e:
            self.logger.error(f"Error fetching tables in schema: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def fetch_all_views_in_schema(
        self, db_session, schema_name: str, pattern: Optional[str] = None
    ) -> List[str]:
        """Fetch all views in a schema."""
        self._validate_schema_name(schema_name)

        try:
            query = f"""
                SELECT table_schema, table_name
                FROM information_schema.views
                WHERE table_schema = '{schema_name}' 
                AND table_name  ILIKE '%{pattern}%'
            """
            self.logger.debug(f"Fetching views in schema: {query}")
            temp1 = time.time()
            result = self._execute_query(db_session, query).fetchall()
            temp2 = time.time()
            self._log_performance("fetch_all_views_in_schema", temp2 - temp1)

            tables_list = []
            if result and len(result) > 0:
                for item in result:
                    tables_list.append(item[1])
            return tables_list
        except Exception as e:
            self.logger.error(f"Error fetching views in schema: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def fetch_table_type_in_schema(
        self, db_session, schema_name: str, table_name: str
    ) -> str:
        """Fetch the type (table or view) of a specified table."""
        self._validate_schema_name(schema_name)
        self._validate_table_name(table_name)

        try:
            query = (
                f"select table_type from information_schema.tables where "
                f"table_schema = '{schema_name}' and table_name = '{table_name}'"
            )
            self.logger.debug(f"Fetching table type: {query}")
            result = self._execute_query(db_session, query).fetchall()

            if result:
                return result[0][0]
            return "VIEW"
        except Exception as e:
            self.logger.error(f"Error fetching table type: {e}")
            raise QueryExecutionError(query, str(e), self.database_type)

    def get_tables_under_schema(self, db_session, schema: str) -> List[str]:
        """Get all tables under a schema."""
        self._validate_schema_name(schema)

        try:
            query = (
                f"SELECT distinct table_name FROM information_schema.tables WHERE table_schema = '{schema}' "
                f"AND table_type = 'BASE TABLE';"
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
        query = f' mode() within group (order by "{column}") '
        if alias:
            query += f'as "{alias}" '
        return query

    def median_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for median function."""
        # PostgreSQL doesn't have a built-in median function
        return ""

    def concat_function(self, column: List[str], alias: str, separator: str) -> str:
        """Generate SQL for concatenation function."""
        return f" || '{separator}' || ".join(column) + f" AS {alias}"

    def pivot_function(
        self,
        fields: Dict[str, Any],
        column_list: List[str],
        schema: str,
        table_name: str,
    ) -> str:
        """Generate SQL for pivot function."""
        column = fields.get("column")
        data_type = fields.get("data_type")
        value_column = fields.get("value_column")
        mappings = fields.get("mappings")
        cases = ""

        for key, value in mappings.items():
            if value.get("status") is True:
                cases += f"""CASE WHEN {column} = {f"'{key}'" if data_type not in NUMERICAL_DATA_TYPES else f"{key}"} THEN {value_column if value_column else "'1'"} ELSE '0' END AS {value.get('value')}, """

        cases = cases[:-2]
        query_string = f"""SELECT {', '.join(column_list)}, {column}, {cases} FROM {schema}.{table_name}"""
        return query_string

    def trim_function(
        self, column: str, value: str, condition: str, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for trim function."""
        if alias:
            return f" TRIM({condition} '{value}' FROM {column}) as {alias} "

        return f" TRIM({condition} '{value}' FROM {column}) "

    def split_function(
        self, column: str, delimiter: str, part: int, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for split function."""
        if alias:
            return f" split_part({column}, '{delimiter}', {part}) as {alias} "

        return f" split_part({column}, '{delimiter}', {part}) "

    def timestamp_to_date_function(
        self, column: str, alias: Optional[str] = None
    ) -> str:
        """Generate SQL for timestamp to date conversion."""
        return f" TRUNC({column}) AS {alias} "

    def substring_function(self, column: str, start: int, end: int) -> str:
        """Generate SQL for substring function."""
        return f" SUBSTRING({column}::TEXT FROM {start} FOR {end}) "

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
        EXTRACT(EPOCH FROM CAST({end_date} AS TIMESTAMP) - CAST({start_date} AS TIMESTAMP)) / 3600 as {alias}
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
        query = f"DATEDIFF({date_part}, {start_date}, {end_date})"
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
                for keyword in REDSHIFT_RESERVED_KEYWORDS:
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
                '"{}"'.format(col) if col in REDSHIFT_RESERVED_KEYWORDS else col
                for col in columns
            ]
            return ", ".join(enclosed_columns)
        except Exception as e:
            self.logger.error(f"Error enclosing reserved keywords v2: {e}")
            return columns_string

    def handle_reserved_keywords(self, query_string: str) -> str:
        """Handle reserved keywords in a query string."""
        # Loop through each reserved keyword and surround them with double quotes in the SQL query
        for keyword in REDSHIFT_RESERVED_KEYWORDS:
            query_string = re.sub(
                rf"\b{keyword}\b", f'"{keyword}"', query_string, flags=re.IGNORECASE
            )
        return query_string
