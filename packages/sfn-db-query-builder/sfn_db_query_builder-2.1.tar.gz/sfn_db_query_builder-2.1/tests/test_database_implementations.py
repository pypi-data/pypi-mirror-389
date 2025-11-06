"""
Test suite for all database implementations.

This test suite validates all database-specific implementations including
PostgreSQL, BigQuery, Redshift, and their specific features and functionality.
"""

import pytest
from unittest.mock import Mock
from sfn_db_query_builder.core.factory import (
    create_query_builder,
    get_supported_database_types,
)
from sfn_db_query_builder.core.exceptions import UnsupportedDatabaseError
from sfn_db_query_builder.implementations.snowflake.sfn_db_query_builder import SnowflakeQueryBuilder
from sfn_db_query_builder.implementations.postgresql.sfn_db_query_builder import (
    PostgresqlQueryBuilder,
)
from sfn_db_query_builder.implementations.bigquery.sfn_db_query_builder import BigqueryQueryBuilder
from sfn_db_query_builder.implementations.redshift.sfn_db_query_builder import RedshiftQueryBuilder


class TestDatabaseImplementations:
    """Test all database implementations."""

    def test_factory_creates_all_implementations(self):
        """Test that the factory can create all supported database implementations."""
        # Test Snowflake
        snowflake_builder = create_query_builder("snowflake")
        assert isinstance(snowflake_builder, SnowflakeQueryBuilder)
        assert snowflake_builder.database_type == "snowflake"

        # Test PostgreSQL
        postgresql_builder = create_query_builder("postgresql")
        assert isinstance(postgresql_builder, PostgresqlQueryBuilder)
        assert postgresql_builder.database_type == "postgresql"

        # Test BigQuery
        bigquery_builder = create_query_builder("bigquery")
        assert isinstance(bigquery_builder, BigqueryQueryBuilder)
        assert bigquery_builder.database_type == "bigquery"

        # Test Redshift
        redshift_builder = create_query_builder("redshift")
        assert isinstance(redshift_builder, RedshiftQueryBuilder)
        assert redshift_builder.database_type == "redshift"

    def test_supported_database_types(self):
        """Test that all expected database types are supported."""
        supported_types = get_supported_database_types()
        expected_types = ["snowflake", "postgresql", "bigquery", "redshift"]

        for db_type in expected_types:
            assert db_type in supported_types

    def test_unsupported_database_raises_error(self):
        """Test that unsupported database types raise appropriate errors."""
        with pytest.raises(UnsupportedDatabaseError):
            create_query_builder("unsupported_db")

        with pytest.raises(UnsupportedDatabaseError):
            create_query_builder("mysql")

        with pytest.raises(UnsupportedDatabaseError):
            create_query_builder("oracle")


class TestPostgreSQLImplementation:
    """Test the PostgreSQL implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = PostgresqlQueryBuilder("postgresql")
        self.mock_session = Mock()
        self.mock_session.execute.return_value.fetchone.return_value = ("test",)
        self.mock_session.execute.return_value.fetchall.return_value = [("test",)]

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
        assert "mode()" in result
        assert "within group" in result
        assert "test_alias" in result

    def test_median_function(self):
        """Test median function generation."""
        result = self.builder.median_function("test_column", "test_alias")
        # PostgreSQL doesn't have a built-in median function
        assert result == ""

    def test_concat_function(self):
        """Test concat function generation."""
        columns = ["col1", "col2", "col3"]
        result = self.builder.concat_function(columns, "test_alias", ",")
        assert "||" in result
        assert "test_alias" in result

    def test_trim_function(self):
        """Test trim function generation."""
        result = self.builder.trim_function(
            "test_column", "test_value", "leading", "test_alias"
        )
        assert "TRIM" in result
        assert "test_alias" in result

    def test_split_function(self):
        """Test split function generation."""
        result = self.builder.split_function("test_column", ",", 2, "test_alias")
        assert "split_part" in result
        assert "test_alias" in result

    def test_timestamp_to_date_function(self):
        """Test timestamp to date function generation."""
        result = self.builder.timestamp_to_date_function("test_column", "test_alias")
        assert "TRUNC" in result
        assert "test_alias" in result

    def test_substring_function(self):
        """Test substring function generation."""
        result = self.builder.substring_function("test_column", 1, 5)
        assert "SUBSTRING" in result

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
        assert "EXTRACT" in result
        assert "EPOCH" in result

    def test_date_substraction(self):
        """Test date subtraction function generation."""
        result = self.builder.date_substraction(
            "DAY", "start_date", "end_date", "alias"
        )
        assert "DATEDIFF" in result
        assert "alias" in result


class TestBigQueryImplementation:
    """Test the BigQuery implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = BigqueryQueryBuilder("bigquery")
        self.mock_session = Mock()
        self.mock_session.execute.return_value.fetchone.return_value = ("test",)
        self.mock_session.execute.return_value.fetchall.return_value = [("test",)]

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
        # BigQuery doesn't have a built-in mode function
        assert result == ""

    def test_median_function(self):
        """Test median function generation."""
        result = self.builder.median_function("test_column", "test_alias")
        # BigQuery doesn't have a built-in median function
        assert result == ""

    def test_concat_function(self):
        """Test concat function generation."""
        columns = ["col1", "col2", "col3"]
        result = self.builder.concat_function(columns, "test_alias", ",")
        assert "CONCAT" in result
        assert "test_alias" in result

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
        assert "EXTRACT" in result
        assert "EPOCH" in result

    def test_date_substraction(self):
        """Test date subtraction function generation."""
        result = self.builder.date_substraction(
            "HOUR", "start_date", "end_date", "alias"
        )
        assert "DATEDIFF" in result
        assert "HOUR" in result
        assert "alias" in result


class TestRedshiftImplementation:
    """Test the Redshift implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = RedshiftQueryBuilder("redshift")
        self.mock_session = Mock()
        self.mock_session.execute.return_value.fetchone.return_value = ("test",)
        self.mock_session.execute.return_value.fetchall.return_value = [("test",)]

    def test_inherits_from_postgresql(self):
        """Test that Redshift inherits from PostgreSQL."""
        assert isinstance(self.builder, PostgresqlQueryBuilder)
        assert self.builder.database_type == "redshift"

    def test_check_if_table_exists(self):
        """Test table existence check."""
        result = self.builder.check_if_table_exists(
            self.mock_session, "test_schema", "test_table"
        )
        assert result is True

    def test_mode_function(self):
        """Test mode function generation."""
        result = self.builder.mode_function("test_column", "test_alias")
        assert "mode()" in result
        assert "within group" in result
        assert "test_alias" in result

    def test_median_function(self):
        """Test median function generation."""
        result = self.builder.median_function("test_column", "test_alias")
        # Redshift doesn't have a built-in median function
        assert result == ""

    def test_concat_function(self):
        """Test concat function generation."""
        columns = ["col1", "col2", "col3"]
        result = self.builder.concat_function(columns, "test_alias", ",")
        assert "||" in result
        assert "test_alias" in result

    def test_trim_function(self):
        """Test trim function generation."""
        result = self.builder.trim_function(
            "test_column", "test_value", "leading", "test_alias"
        )
        assert "TRIM" in result
        assert "test_alias" in result

    def test_split_function(self):
        """Test split function generation."""
        result = self.builder.split_function("test_column", ",", 2, "test_alias")
        assert "split_part" in result
        assert "test_alias" in result

    def test_timestamp_to_date_function(self):
        """Test timestamp to date function generation."""
        result = self.builder.timestamp_to_date_function("test_column", "test_alias")
        assert "TRUNC" in result
        assert "test_alias" in result

    def test_substring_function(self):
        """Test substring function generation."""
        result = self.builder.substring_function("test_column", 1, 5)
        assert "SUBSTRING" in result

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
        assert "EXTRACT" in result
        assert "EPOCH" in result

    def test_date_substraction(self):
        """Test date subtraction function generation."""
        result = self.builder.date_substraction(
            "DAY", "start_date", "end_date", "alias"
        )
        assert "DATEDIFF" in result
        assert "alias" in result


class TestDatabaseSpecificFeatures:
    """Test database-specific features and configurations."""

    def test_snowflake_features(self):
        """Test Snowflake-specific features."""
        from sfn_db_query_builder.config.database_types import get_database_config

        config = get_database_config("snowflake")
        assert config["case_sensitive"] is False
        assert config["supports_views"] is True
        assert config["supports_pivot"] is True
        assert config["supports_mode"] is True
        assert config["supports_median"] is True

    def test_postgresql_features(self):
        """Test PostgreSQL-specific features."""
        from sfn_db_query_builder.config.database_types import get_database_config

        config = get_database_config("postgresql")
        assert config["case_sensitive"] is True
        assert config["supports_views"] is True
        assert config["supports_pivot"] is True
        assert config["supports_mode"] is True
        assert config["supports_median"] is False

    def test_bigquery_features(self):
        """Test BigQuery-specific features."""
        from sfn_db_query_builder.config.database_types import get_database_config

        config = get_database_config("bigquery")
        assert config["case_sensitive"] is False
        assert config["identifier_quote"] == "`"
        assert config["supports_views"] is True
        assert config["supports_pivot"] is False
        assert config["supports_mode"] is False
        assert config["supports_median"] is False

    def test_redshift_features(self):
        """Test Redshift-specific features."""
        from sfn_db_query_builder.config.database_types import get_database_config

        config = get_database_config("redshift")
        assert config["case_sensitive"] is True
        assert config["supports_views"] is True
        assert config["supports_pivot"] is True
        assert config["supports_mode"] is True
        assert config["supports_median"] is False


if __name__ == "__main__":
    pytest.main([__file__])
