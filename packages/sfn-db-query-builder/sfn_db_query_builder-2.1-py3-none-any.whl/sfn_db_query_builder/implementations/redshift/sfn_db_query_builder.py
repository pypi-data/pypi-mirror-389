"""
Redshift query builder implementation.

This module provides the Redshift-specific implementation of the query builder interface.
Redshift extends PostgreSQL functionality with some specific differences and optimizations.
"""

from typing import List, Optional

from ...config.constants import REDSHIFT_RESERVED_KEYWORDS
from ..postgresql.sfn_db_query_builder import PostgresqlQueryBuilder


class RedshiftQueryBuilder(PostgresqlQueryBuilder):
    """Redshift-specific query builder implementation.

    Redshift extends PostgreSQL functionality, so we inherit from PostgresqlQueryBuilder
    and override specific methods where Redshift behavior differs.
    """

    def __init__(self, database_type: str):
        super().__init__(database_type)
        # Redshift-specific configuration overrides
        self.config.update(
            {
                "supports_median": False,  # Redshift doesn't support median function
                "supports_mode": True,  # Redshift supports mode function
            }
        )

    def median_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for median function.

        Redshift doesn't have a built-in median function, so we return an empty string.
        """
        return ""

    def mode_function(self, column: str, alias: Optional[str] = None) -> str:
        """Generate SQL for mode function.

        Redshift uses the same mode function syntax as PostgreSQL.
        """
        return super().mode_function(column, alias)

    def date_substraction(
        self,
        date_part: str,
        start_date: str,
        end_date: str,
        alias: Optional[str] = None,
    ) -> str:
        """Generate SQL for date subtraction.

        Redshift uses DATEDIFF function similar to PostgreSQL.
        """
        return super().date_substraction(date_part, start_date, end_date, alias)

    def date_diff_in_hours(
        self, start_date: str, end_date: str, table_name: str, alias: str
    ) -> str:
        """Generate SQL for date difference in hours.

        Redshift uses EXTRACT with EPOCH similar to PostgreSQL.
        """
        return super().date_diff_in_hours(start_date, end_date, table_name, alias)

    def enclose_reserved_keywords(self, query: str) -> str:
        """Enclose reserved keywords in a query.

        Redshift has specific reserved keywords that need to be handled.
        """
        try:
            import re

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
        """Enclose reserved keywords in a column string.

        Redshift-specific reserved keyword handling.
        """
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
        """Handle reserved keywords in a query string.

        Redshift-specific reserved keyword handling.
        """
        import re

        # Loop through each reserved keyword and surround them with double quotes in the SQL query
        for keyword in REDSHIFT_RESERVED_KEYWORDS:
            query_string = re.sub(
                rf"\b{keyword}\b", f'"{keyword}"', query_string, flags=re.IGNORECASE
            )
        return query_string

    def get_schemas_like_pattern(
        self,
        db_session,
        schema_name: Optional[str] = None,
        source_database: Optional[str] = None,
    ) -> List[str]:
        """Get schemas matching a pattern.

        Redshift uses the same schema query pattern as PostgreSQL.
        """
        return super().get_schemas_like_pattern(
            db_session, schema_name, source_database
        )

    def fetch_all_views_in_schema(
        self, db_session, schema_name: str, pattern: Optional[str] = None
    ) -> List[str]:
        """Fetch all views in a schema.

        Redshift uses the same view query pattern as PostgreSQL.
        """
        return super().fetch_all_views_in_schema(db_session, schema_name, pattern)

    def fetch_table_type_in_schema(
        self, db_session, schema_name: str, table_name: str
    ) -> str:
        """Fetch the type (table or view) of a specified table.

        Redshift uses the same table type query pattern as PostgreSQL.
        """
        return super().fetch_table_type_in_schema(db_session, schema_name, table_name)
