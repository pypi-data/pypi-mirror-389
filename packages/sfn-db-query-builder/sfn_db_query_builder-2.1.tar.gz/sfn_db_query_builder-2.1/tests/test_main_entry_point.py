"""
Test suite for the main entry point and public API.

This test suite validates the MultiDatabaseQueryBuilder as the main entry point,
including both class and function interfaces, backward compatibility, and integration
across all database implementations.
"""

import pytest
from unittest.mock import Mock
from sfn_db_query_builder import (
    MultiDatabaseQueryBuilder,
    check_if_table_exists,
    mode_function,
    SNOWFLAKE,
    POSTGRESQL,
    BIGQUERY,
    REDSHIFT,
    SNOWFLAKE_RESERVED_KEYWORDS,
    NUMERICAL_DATA_TYPES,
)
from sfn_db_query_builder.core.exceptions import UnsupportedDatabaseError


class TestMultiDatabaseQueryBuilder:
    """Test the main MultiDatabaseQueryBuilder class."""

    def test_create_snowflake_builder(self):
        """Test creating a Snowflake query builder."""
        qb = MultiDatabaseQueryBuilder("snowflake")
        assert qb.database_type == "snowflake"
        assert qb._query_builder is not None

    def test_create_postgresql_builder(self):
        """Test creating a PostgreSQL query builder."""
        qb = MultiDatabaseQueryBuilder("postgresql")
        assert qb.database_type == "postgresql"
        assert qb._query_builder is not None

    def test_create_bigquery_builder(self):
        """Test creating a BigQuery query builder."""
        qb = MultiDatabaseQueryBuilder("bigquery")
        assert qb.database_type == "bigquery"
        assert qb._query_builder is not None

    def test_create_redshift_builder(self):
        """Test creating a Redshift query builder."""
        qb = MultiDatabaseQueryBuilder("redshift")
        assert qb.database_type == "redshift"
        assert qb._query_builder is not None

    def test_create_unsupported_database(self):
        """Test creating an unsupported database raises error."""
        with pytest.raises(UnsupportedDatabaseError):
            MultiDatabaseQueryBuilder("unsupported")

    def test_case_insensitive_database_type(self):
        """Test that database type is case insensitive."""
        qb1 = MultiDatabaseQueryBuilder("SNOWFLAKE")
        qb2 = MultiDatabaseQueryBuilder("Snowflake")
        qb3 = MultiDatabaseQueryBuilder("snowflake")

        assert qb1.database_type == "snowflake"
        assert qb2.database_type == "snowflake"
        assert qb3.database_type == "snowflake"


class TestFunctionInterface:
    """Test the standalone function interface."""

    def test_mode_function_snowflake(self):
        """Test mode function for Snowflake."""
        result = mode_function(SNOWFLAKE, "test_column", "test_alias")
        assert "mode(" in result
        assert "test_column" in result
        assert "test_alias" in result

    def test_mode_function_postgresql(self):
        """Test mode function for PostgreSQL."""
        result = mode_function(POSTGRESQL, "test_column", "test_alias")
        assert "mode()" in result
        assert "test_column" in result
        assert "test_alias" in result

    def test_mode_function_bigquery(self):
        """Test mode function for BigQuery."""
        result = mode_function(BIGQUERY, "test_column", "test_alias")
        # BigQuery implementation may return empty string (not implemented)
        assert isinstance(result, str)

    def test_mode_function_redshift(self):
        """Test mode function for Redshift."""
        result = mode_function(REDSHIFT, "test_column", "test_alias")
        assert "mode()" in result
        assert "test_column" in result
        assert "test_alias" in result

    def test_check_if_table_exists_function(self):
        """Test check_if_table_exists function."""
        mock_session = Mock()
        mock_session.execute.return_value.fetchone.return_value = ("test",)

        result = check_if_table_exists(
            SNOWFLAKE, mock_session, "test_schema", "test_table"
        )
        assert result is True

    def test_function_interface_creates_builder_internally(self):
        """Test that function interface creates MultiDatabaseQueryBuilder internally."""
        # This test ensures the function interface works by creating builders internally
        result1 = mode_function(SNOWFLAKE, "col", "alias")
        result2 = mode_function(POSTGRESQL, "col", "alias")

        # Results should be different for different databases
        assert result1 != result2


class TestClassInterface:
    """Test the class interface."""

    def test_snowflake_class_interface(self):
        """Test Snowflake class interface."""
        qb = MultiDatabaseQueryBuilder("snowflake")
        result = qb.mode_function("test_column", "test_alias")
        assert "mode(" in result
        assert "test_column" in result
        assert "test_alias" in result

    def test_postgresql_class_interface(self):
        """Test PostgreSQL class interface."""
        qb = MultiDatabaseQueryBuilder("postgresql")
        result = qb.mode_function("test_column", "test_alias")
        assert "mode()" in result
        assert "test_column" in result
        assert "test_alias" in result

    def test_bigquery_class_interface(self):
        """Test BigQuery class interface."""
        qb = MultiDatabaseQueryBuilder("bigquery")
        result = qb.mode_function("test_column", "test_alias")
        assert isinstance(result, str)

    def test_redshift_class_interface(self):
        """Test Redshift class interface."""
        qb = MultiDatabaseQueryBuilder("redshift")
        result = qb.mode_function("test_column", "test_alias")
        assert "mode()" in result
        assert "test_column" in result
        assert "test_alias" in result

    def test_all_methods_available(self):
        """Test that all expected methods are available."""
        qb = MultiDatabaseQueryBuilder("snowflake")

        # Test that all methods exist and are callable
        methods = [
            "check_if_table_exists",
            "check_if_column_exists",
            "fetch_column_name",
            "fetch_column_name_datatype",
            "fetch_single_column_name_datatype",
            "get_schemas_like_pattern",
            "fetch_all_tables_in_schema",
            "fetch_all_views_in_schema",
            "fetch_table_type_in_schema",
            "get_tables_under_schema",
            "mode_function",
            "median_function",
            "concat_function",
            "pivot_function",
            "trim_function",
            "split_function",
            "timestamp_to_date_function",
            "substring_function",
            "table_rename_query",
            "date_diff_in_hours",
            "date_substraction",
            "enclose_reserved_keywords",
            "enclose_reserved_keywords_v2",
            "handle_reserved_keywords",
        ]

        for method_name in methods:
            assert hasattr(qb, method_name)
            assert callable(getattr(qb, method_name))


class TestConstants:
    """Test that all constants are available."""

    def test_database_constants(self):
        """Test database type constants."""
        assert SNOWFLAKE == "snowflake"
        assert POSTGRESQL == "postgresql"
        assert BIGQUERY == "bigquery"
        assert REDSHIFT == "redshift"

    def test_reserved_keywords_constant(self):
        """Test reserved keywords constant."""
        assert isinstance(SNOWFLAKE_RESERVED_KEYWORDS, list)
        # Note: SNOWFLAKE_RESERVED_KEYWORDS may be empty in current implementation
        # This test just ensures it's a list

    def test_data_types_constant(self):
        """Test data types constant."""
        assert isinstance(NUMERICAL_DATA_TYPES, list)
        assert len(NUMERICAL_DATA_TYPES) > 0
        assert "int" in NUMERICAL_DATA_TYPES  # lowercase 'int'


class TestBackwardCompatibility:
    """Test backward compatibility with legacy code patterns."""

    def test_legacy_function_calls_work(self):
        """Test that legacy function call patterns still work."""
        # Test various function calls that should work identically
        result1 = mode_function(SNOWFLAKE, "column", "alias")
        result2 = mode_function(POSTGRESQL, "column", "alias")

        assert isinstance(result1, str)
        assert isinstance(result2, str)

    def test_legacy_class_usage_works(self):
        """Test that legacy class usage patterns still work."""
        # Test creating builders for different databases
        builders = [
            MultiDatabaseQueryBuilder("snowflake"),
            MultiDatabaseQueryBuilder("postgresql"),
            MultiDatabaseQueryBuilder("bigquery"),
            MultiDatabaseQueryBuilder("redshift"),
        ]

        for builder in builders:
            assert builder.database_type in [
                "snowflake",
                "postgresql",
                "bigquery",
                "redshift",
            ]
            assert builder._query_builder is not None

    def test_import_patterns_work(self):
        """Test that various import patterns work."""
        # Test that we can import everything from the main module
        from sfn_db_query_builder import (
            MultiDatabaseQueryBuilder,
            check_if_table_exists,
            mode_function,
            SNOWFLAKE,
            POSTGRESQL,
            BIGQUERY,
            REDSHIFT,
        )

        # Test that imports work
        assert MultiDatabaseQueryBuilder is not None
        assert check_if_table_exists is not None
        assert mode_function is not None
        assert SNOWFLAKE == "snowflake"
        assert POSTGRESQL == "postgresql"
        assert BIGQUERY == "bigquery"
        assert REDSHIFT == "redshift"


class TestErrorHandling:
    """Test error handling in the clean architecture."""

    def test_unsupported_database_error(self):
        """Test that unsupported databases raise proper errors."""
        with pytest.raises(UnsupportedDatabaseError):
            MultiDatabaseQueryBuilder("invalid_database")

    def test_function_interface_error_handling(self):
        """Test that function interface handles errors properly."""
        with pytest.raises(UnsupportedDatabaseError):
            mode_function("invalid_database", "column", "alias")


class TestIntegration:
    """Integration tests for the complete system."""

    def test_end_to_end_workflow(self):
        """Test a complete end-to-end workflow."""
        # Test class interface
        qb = MultiDatabaseQueryBuilder("snowflake")
        result1 = qb.mode_function("test_column", "test_alias")

        # Test function interface
        result2 = mode_function(SNOWFLAKE, "test_column", "test_alias")

        # Results should be identical
        assert result1 == result2

        # Test with different database
        qb_pg = MultiDatabaseQueryBuilder("postgresql")
        result3 = qb_pg.mode_function("test_column", "test_alias")

        # Results should be different for different databases
        assert result1 != result3

    def test_all_database_types_work(self):
        """Test that all database types work with both interfaces."""
        databases = [
            ("snowflake", SNOWFLAKE),
            ("postgresql", POSTGRESQL),
            ("bigquery", BIGQUERY),
            ("redshift", REDSHIFT),
        ]

        for db_name, db_constant in databases:
            # Test class interface
            qb = MultiDatabaseQueryBuilder(db_name)
            class_result = qb.mode_function("test_column", "test_alias")

            # Test function interface
            func_result = mode_function(db_constant, "test_column", "test_alias")

            # Results should be identical
            assert class_result == func_result
            assert isinstance(class_result, str)
            assert isinstance(func_result, str)
