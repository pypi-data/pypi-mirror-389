"""
Tests for QueryBuilder class in Holo Search SDK.

This module contains comprehensive tests for QueryBuilder functionality including
query construction, method chaining, and SQL generation.
"""

from unittest.mock import Mock

import pytest
from psycopg import sql as psql

from holo_search_sdk.backend.connection import HoloConnect
from holo_search_sdk.backend.query import QueryBuilder
from holo_search_sdk.exceptions import SqlError


class TestQueryBuilder:
    """Test cases for the QueryBuilder class."""

    def test_query_builder_initialization(self):
        """Test QueryBuilder initialization."""
        mock_connection = Mock(spec=HoloConnect)
        table_name = "test_table"

        query_builder = QueryBuilder(mock_connection, table_name)

        assert query_builder._connection is mock_connection
        assert query_builder._table_name == table_name
        assert query_builder._limit is None
        assert query_builder._offset == 0
        assert query_builder._filters == []
        assert query_builder._select_fields == []
        assert query_builder._order_by is None
        assert query_builder._group_by is None
        assert query_builder._sort_order == "desc"

    def test_limit_method(self):
        """Test limit method."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.limit(10)

        assert result is query_builder  # Method chaining
        assert query_builder._limit == 10

    def test_offset_method(self):
        """Test offset method."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.offset(5)

        assert result is query_builder  # Method chaining
        assert query_builder._offset == 5

    def test_where_method(self):
        """Test where method."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.where("id > 10")

        assert result is query_builder  # Method chaining
        assert len(query_builder._filters) == 1
        assert query_builder._filters[0].as_string() == "id > 10"

    def test_where_method_multiple_filters(self):
        """Test where method with multiple filters."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.where("id > 10").where("name = 'test'")

        assert len(query_builder._filters) == 2
        expected_filters = [
            "id > 10",
            "name = 'test'",
        ]
        assert all(psql.SQL(f) in query_builder._filters for f in expected_filters)

    def test_select_method_with_string(self):
        """Test select method with string column."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.select("id")

        assert result is query_builder  # Method chaining
        assert len(query_builder._select_fields) == 1
        assert query_builder._select_fields[0] == (psql.SQL("id"), None)

    def test_select_method_with_list(self):
        """Test select method with list of columns."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.select(["id", "name", "email"])

        assert result is query_builder  # Method chaining
        assert len(query_builder._select_fields) == 3
        expected_fields = [
            (psql.SQL("id"), None),
            (psql.SQL("name"), None),
            (psql.SQL("email"), None),
        ]
        assert query_builder._select_fields == expected_fields

    def test_select_method_with_dict(self):
        """Test select method with dictionary (column aliases)."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.select({"id": "user_id", "name": "user_name"})

        assert result is query_builder  # Method chaining
        assert len(query_builder._select_fields) == 2
        expected_fields = [
            (psql.SQL("id"), psql.SQL("user_id")),
            (psql.SQL("name"), psql.SQL("user_name")),
        ]
        # Check that fields contain SQL objects with correct aliases
        assert all(f in query_builder._select_fields for f in expected_fields)

    def test_select_method_multiple_calls(self):
        """Test select method with multiple calls."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select("id").select(["name", "email"]).select({"age": "user_age"})

        assert len(query_builder._select_fields) == 4
        # Check that all fields are present
        expected_fields = [
            (psql.SQL("id"), None),
            (psql.SQL("name"), None),
            (psql.SQL("email"), None),
            (psql.SQL("age"), psql.SQL("user_age")),
        ]
        assert all(f in query_builder._select_fields for f in expected_fields)

    def test_order_by_method_default_desc(self):
        """Test order_by method with default desc order."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.order_by("created_at")

        assert result is query_builder  # Method chaining
        assert query_builder._order_by.as_string() == "created_at"
        assert query_builder._sort_order == "desc"

    def test_order_by_method_with_asc_order(self):
        """Test order_by method with asc order."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.order_by("name", "asc")

        assert result is query_builder  # Method chaining
        assert query_builder._order_by.as_string() == "name"
        assert query_builder._sort_order == "asc"

    def test_group_by_method(self):
        """Test group_by method."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.group_by("category")

        assert result is query_builder  # Method chaining
        assert query_builder._group_by.as_string() == "category"

    def test_generate_sql_simple_select(self):
        """Test SQL generation for simple select."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"])
        sql = query_builder._generate_sql()
        assert sql.as_string() == 'SELECT id, name FROM "test_table" OFFSET 0;'

    def test_generate_sql_with_aliases(self):
        """Test SQL generation with column aliases."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select({"id": "user_id", "name": "user_name"})
        sql = query_builder._generate_sql()
        assert (
            sql.as_string()
            == 'SELECT id AS user_id, name AS user_name FROM "test_table" OFFSET 0;'
        )

    def test_generate_sql_with_where_clause(self):
        """Test SQL generation with WHERE clause."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"]).where("id > 10").where("status = 'active'")
        sql = query_builder._generate_sql()
        assert (
            sql.as_string()
            == "SELECT id, name FROM \"test_table\" WHERE id > 10 AND status = 'active' OFFSET 0;"
        )

    def test_generate_sql_with_group_by(self):
        """Test SQL generation with GROUP BY clause."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["category", "COUNT(*)"]).group_by("category")
        sql = query_builder._generate_sql()
        assert (
            sql.as_string()
            == 'SELECT category, COUNT(*) FROM "test_table" GROUP BY category OFFSET 0;'
        )

    def test_generate_sql_with_order_by(self):
        """Test SQL generation with ORDER BY clause."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"]).order_by("created_at", "desc")
        sql = query_builder._generate_sql()
        assert (
            sql.as_string()
            == 'SELECT id, name FROM "test_table" ORDER BY created_at DESC OFFSET 0;'
        )

    def test_generate_sql_with_limit_and_offset(self):
        """Test SQL generation with LIMIT and OFFSET."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"]).limit(10).offset(20)
        sql = query_builder._generate_sql()
        assert (
            sql.as_string() == 'SELECT id, name FROM "test_table" LIMIT 10 OFFSET 20;'
        )

    def test_generate_sql_complex_query(self):
        """Test SQL generation for complex query with all clauses."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "users")

        query_builder.select(
            {"id": "user_id", "name": "user_name", "email": None}
        ).where("age > 18").where("status = 'active'").group_by("department").order_by(
            "created_at", "asc"
        ).limit(
            50
        ).offset(
            100
        )

        sql = query_builder._generate_sql()
        assert (
            sql.as_string()
            == "SELECT id AS user_id, name AS user_name, email FROM \"users\" WHERE age > 18 AND status = 'active' GROUP BY department ORDER BY created_at ASC LIMIT 50 OFFSET 100;"
        )

    def test_generate_sql_no_select_fields_raises_error(self):
        """Test that SQL generation raises error when no select fields are set."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        with pytest.raises(SqlError) as exc_info:
            query_builder._generate_sql()

        assert "Select fields is not set" in str(exc_info.value)

    def test_submit_method(self):
        """Test submit method."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"])
        query_builder.submit()

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args[0]
        expected_sql = 'SELECT id, name FROM "test_table" OFFSET 0;'
        assert call_args[0].as_string() == expected_sql

    def test_fetchone_method(self):
        """Test fetchone method."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.fetchone.return_value = (1, "test_name")
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"])
        result = query_builder.fetchone()

        mock_connection.fetchone.assert_called_once()
        call_args = mock_connection.fetchone.call_args[0]
        expected_sql = 'SELECT id, name FROM "test_table" OFFSET 0;'
        assert call_args[0].as_string() == expected_sql

    def test_fetchall_method(self):
        """Test fetchall method."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.fetchall.return_value = [(1, "test1"), (2, "test2")]
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"])
        result = query_builder.fetchall()

        mock_connection.fetchall.assert_called_once()
        call_args = mock_connection.fetchall.call_args[0]
        expected_sql = 'SELECT id, name FROM "test_table" OFFSET 0;'
        assert call_args[0].as_string() == expected_sql

    def test_fetchmany_method_default_size(self):
        """Test fetchmany method with default size."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.fetchmany.return_value = [(1, "test1"), (2, "test2")]
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"])
        result = query_builder.fetchmany()

        # Verify that fetchmany was called with correct parameters
        mock_connection.fetchmany.assert_called_once()
        call_args = mock_connection.fetchmany.call_args
        expected_sql = 'SELECT id, name FROM "test_table" OFFSET 0;'
        assert call_args[0][0].as_string() == expected_sql
        assert call_args[1]["params"] is None
        assert call_args[1]["size"] == 0
        assert result == [(1, "test1"), (2, "test2")]

    def test_fetchmany_method_with_size(self):
        """Test fetchmany method with specific size."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.fetchmany.return_value = [(1, "test1")]
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"])
        result = query_builder.fetchmany(size=1)

        # Verify that fetchmany was called with correct parameters
        mock_connection.fetchmany.assert_called_once()
        call_args = mock_connection.fetchmany.call_args
        expected_sql = 'SELECT id, name FROM "test_table" OFFSET 0;'
        assert call_args[0][0].as_string() == expected_sql
        assert call_args[1]["params"] is None
        assert call_args[1]["size"] == 1
        assert result == [(1, "test1")]

    def test_method_chaining(self):
        """Test method chaining functionality."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        # Test that all methods return self for chaining
        result = (
            query_builder.select(["id", "name"])
            .where("id > 10")
            .order_by("name", "asc")
            .group_by("category")
            .limit(20)
            .offset(10)
        )

        assert result is query_builder
        assert len(query_builder._select_fields) == 2
        expected_fields = [(psql.SQL("id"), None), (psql.SQL("name"), None)]
        assert all(f in query_builder._select_fields for f in expected_fields)
        assert len(query_builder._filters) == 1
        assert query_builder._filters[0].as_string() == "id > 10"
        assert query_builder._order_by.as_string() == "name"
        assert query_builder._sort_order == "asc"
        assert query_builder._group_by.as_string() == "category"
        assert query_builder._limit == 20
        assert query_builder._offset == 10

    def test_limit_with_zero(self):
        """Test limit method with zero value."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.limit(0)

        assert result is query_builder
        assert query_builder._limit == 0

    def test_offset_with_zero(self):
        """Test offset method with zero value."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.offset(0)

        assert result is query_builder
        assert query_builder._offset == 0

    def test_select_empty_list(self):
        """Test select method with empty list."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.select([])

        assert result is query_builder
        assert query_builder._select_fields == []

    def test_select_empty_dict(self):
        """Test select method with empty dictionary."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.select({})

        assert result is query_builder
        assert query_builder._select_fields == []

    def test_order_by_with_invalid_order(self):
        """Test order_by method with custom order value."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        result = query_builder.order_by("name", "custom_order")

        assert result is query_builder
        assert query_builder._order_by.as_string() == "name"
        assert query_builder._sort_order == "custom_order"

    def test_sql_generation_with_special_characters_in_filters(self):
        """Test SQL generation with special characters in filter conditions."""
        mock_connection = Mock(spec=HoloConnect)
        query_builder = QueryBuilder(mock_connection, "test_table")

        query_builder.select(["id", "name"]).where("name LIKE '%test%'").where(
            "id IN (1,2,3)"
        )
        sql = query_builder._generate_sql()
        assert (
            sql.as_string()
            == """SELECT id, name FROM "test_table" WHERE name LIKE '%test%' AND id IN (1,2,3) OFFSET 0;"""
        )
