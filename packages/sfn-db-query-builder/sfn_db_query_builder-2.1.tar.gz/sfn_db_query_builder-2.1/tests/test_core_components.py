"""
Test suite for core components and infrastructure.

This test suite validates the core components including factory pattern,
database type management, configuration, error handling, and the Snowflake
implementation as a reference implementation.
"""

import pytest
from unittest.mock import Mock
from sfn_db_query_builder.core.factory import (
    create_query_builder,
    get_supported_database_types,
)
from sfn_db_query_builder.core.exceptions import UnsupportedDatabaseError
from sfn_db_query_builder.config.database_types import DatabaseType
from sfn_db_query_builder.implementations.snowflake.sfn_db_query_builder import SnowflakeQueryBuilder


class TestCoreComponents:
    """Test the core components and infrastructure."""

    def test_factory_creation(self):
        """Test that the factory can create query builders."""
        # Test supported database types
        supported_types = get_supported_database_types()
        assert "snowflake" in supported_types
        assert "postgresql" in supported_types
        assert "bigquery" in supported_types
        assert "redshift" in supported_types

    def test_create_snowflake_builder(self):
        """Test creating a Snowflake query builder."""
        builder = create_query_builder("snowflake")
        assert isinstance(builder, SnowflakeQueryBuilder)
        assert builder.database_type == "snowflake"

    def test_create_unsupported_database(self):
        """Test creating an unsupported database type raises error."""
        with pytest.raises(UnsupportedDatabaseError):
            create_query_builder("unsupported_db")

    def test_database_type_enum(self):
        """Test database type enum functionality."""
        assert DatabaseType.SNOWFLAKE.value == "snowflake"
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.BIGQUERY.value == "bigquery"
        assert DatabaseType.REDSHIFT.value == "redshift"

        # Test validation
        assert DatabaseType.is_supported("snowflake")
        assert DatabaseType.is_supported("postgresql")
        assert not DatabaseType.is_supported("unsupported")

        # Test normalization
        assert DatabaseType.validate("SNOWFLAKE") == "snowflake"
        assert DatabaseType.validate("PostgreSQL") == "postgresql"

        with pytest.raises(ValueError):
            DatabaseType.validate("unsupported")


class TestSnowflakeImplementation:
    """Test the Snowflake implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = SnowflakeQueryBuilder("snowflake")
        self.mock_session = Mock()
        self.mock_session.execute.return_value.fetchone.return_value = ("test",)
        self.mock_session.execute.return_value.fetchall.return_value = [("test",)]

    def test_convert_to_upper(self):
        """Test schema and table name conversion to uppercase."""
        schema, table = self.builder.convert_to_upper("test_schema", "test_table")
        assert schema == "TEST_SCHEMA"
        assert table == "TEST_TABLE"

    def test_check_if_table_exists(self):
        """Test table existence check."""
        result = self.builder.check_if_table_exists(
            self.mock_session, "test_schema", "test_table"
        )
        assert result is True

    def test_check_if_table_exists_false(self):
        """Test table existence check when table doesn't exist."""
        self.mock_session.execute.return_value.fetchone.return_value = None
        result = self.builder.check_if_table_exists(
            self.mock_session, "test_schema", "test_table"
        )
        assert result is False

    def test_mode_function(self):
        """Test mode function generation."""
        result = self.builder.mode_function("test_column", "test_alias")
        assert 'mode("test_column")' in result
        assert 'as "test_alias"' in result

    def test_median_function(self):
        """Test median function generation."""
        result = self.builder.median_function("test_column", "test_alias")
        assert 'median("test_column")' in result
        assert 'as "test_alias"' in result

    def test_concat_function(self):
        """Test concat function generation."""
        columns = ["col1", "col2", "col3"]
        result = self.builder.concat_function(columns, "test_alias", ",")
        assert "CONCAT_WS" in result
        assert "test_alias" in result

    def test_trim_function(self):
        """Test trim function generation."""
        result = self.builder.trim_function(
            "test_column", "test_value", "leading", "test_alias"
        )
        assert "REGEXP_REPLACE" in result
        assert "test_alias" in result

    def test_split_function(self):
        """Test split function generation."""
        result = self.builder.split_function("test_column", ",", 2, "test_alias")
        assert "split_part" in result
        assert "test_alias" in result

    def test_timestamp_to_date_function(self):
        """Test timestamp to date function generation."""
        result = self.builder.timestamp_to_date_function("test_column", "test_alias")
        assert "TO_DATE" in result
        assert "test_alias" in result

    def test_substring_function(self):
        """Test substring function generation."""
        result = self.builder.substring_function("test_column", 1, 5)
        assert "SUBSTR" in result

    def test_table_rename_query(self):
        """Test table rename query generation."""
        result = self.builder.table_rename_query("schema", "old_table", "new_table")
        assert "ALTER TABLE" in result
        assert "RENAME TO" in result

    def test_date_diff_in_hours(self):
        """Test date difference in hours function generation."""
        result = self.builder.date_diff_in_hours(
            "start_date", "end_date", "table_name", "alias"
        )
        assert "DATEDIFF" in result
        assert "HOUR" in result

    def test_date_substraction(self):
        """Test date subtraction function generation."""
        result = self.builder.date_substraction(
            "DAY", "start_date", "end_date", "alias"
        )
        assert "DATEDIFF" in result
        assert "DAY" in result

    def test_enclose_reserved_keywords(self):
        """Test reserved keyword handling."""
        query = "SELECT time FROM table"
        result = self.builder.enclose_reserved_keywords(query)
        # Should return the same query since no reserved keywords are defined for Snowflake
        assert result == query

    def test_enclose_reserved_keywords_v2(self):
        """Test reserved keyword handling v2."""
        columns = "col1, col2, col3"
        result = self.builder.enclose_reserved_keywords_v2(columns)
        assert result == columns

    def test_handle_reserved_keywords(self):
        """Test reserved keyword handling."""
        query = "SELECT time FROM table"
        result = self.builder.handle_reserved_keywords(query)
        # Should return the same query since no reserved keywords are defined for Snowflake
        assert result == query


class TestConfiguration:
    """Test configuration management."""

    def test_database_config(self):
        """Test database configuration."""
        from sfn_db_query_builder.config.database_types import get_database_config

        snowflake_config = get_database_config("snowflake")
        assert snowflake_config["case_sensitive"] is False
        assert snowflake_config["identifier_quote"] == '"'
        assert snowflake_config["supports_views"] is True
        assert snowflake_config["supports_pivot"] is True
        assert snowflake_config["supports_mode"] is True
        assert snowflake_config["supports_median"] is True

    def test_constants(self):
        """Test constants are properly defined."""
        from sfn_db_query_builder.config.constants import (
            NUMERICAL_DATA_TYPES,
            SNOWFLAKE_RESERVED_KEYWORDS,
            REDSHIFT_RESERVED_KEYWORDS,
            BIGQUERY_RESERVED_KEYWORDS,
        )

        assert isinstance(NUMERICAL_DATA_TYPES, list)
        assert "integer" in NUMERICAL_DATA_TYPES
        assert "decimal" in NUMERICAL_DATA_TYPES

        assert isinstance(SNOWFLAKE_RESERVED_KEYWORDS, list)
        assert isinstance(REDSHIFT_RESERVED_KEYWORDS, list)
        assert isinstance(BIGQUERY_RESERVED_KEYWORDS, list)


class TestErrorHandling:
    """Test error handling in the new structure."""

    def test_unsupported_database_error(self):
        """Test unsupported database error."""
        from sfn_db_query_builder.core.exceptions import UnsupportedDatabaseError

        error = UnsupportedDatabaseError("unsupported_db", ["snowflake", "postgresql"])
        assert "Unsupported database type: unsupported_db" in str(error)
        assert error.details["database_type"] == "unsupported_db"
        assert error.details["supported_types"] == ["snowflake", "postgresql"]

    def test_validation_error(self):
        """Test validation error."""
        from sfn_db_query_builder.core.exceptions import ValidationError

        error = ValidationError("schema_name", "", "Schema name cannot be empty")
        assert "Validation failed for field 'schema_name'" in str(error)
        assert error.details["field"] == "schema_name"
        assert error.details["value"] == ""
        assert error.details["reason"] == "Schema name cannot be empty"

    def test_query_execution_error(self):
        """Test query execution error."""
        from sfn_db_query_builder.core.exceptions import QueryExecutionError

        error = QueryExecutionError(
            "SELECT * FROM table", "Connection failed", "snowflake"
        )
        assert "Query execution failed: Connection failed" in str(error)
        assert error.details["query"] == "SELECT * FROM table"
        assert error.details["error"] == "Connection failed"
        assert error.details["database_type"] == "snowflake"


if __name__ == "__main__":
    pytest.main([__file__])
