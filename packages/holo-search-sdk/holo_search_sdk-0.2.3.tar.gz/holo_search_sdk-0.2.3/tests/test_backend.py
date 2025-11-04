"""
Tests for backend modules in Holo Search SDK.

This module contains comprehensive tests for HoloDB and HoloTable classes.
"""

from unittest.mock import Mock, patch

import pytest

from holo_search_sdk.backend import HoloDB, HoloTable
from holo_search_sdk.backend.connection import HoloConnect
from holo_search_sdk.backend.query import QueryBuilder
from holo_search_sdk.exceptions import ConnectionError, QueryError, SqlError, TableError


class TestHoloDB:
    """Test cases for the HoloDB class."""

    def test_holo_db_initialization(self, sample_connection_config):
        """Test HoloDB initialization."""
        db = HoloDB(sample_connection_config)

        assert db._config == sample_connection_config
        assert db._connection is None
        assert db._connected is False

    @patch("holo_search_sdk.backend.database.HoloConnect")
    def test_connect_success(self, mock_holo_connect_class, sample_connection_config):
        """Test successful database connection."""
        mock_connection = Mock(spec=HoloConnect)
        mock_holo_connect_instance = Mock()
        mock_holo_connect_instance.connect.return_value = mock_connection
        mock_holo_connect_class.return_value = mock_holo_connect_instance

        db = HoloDB(sample_connection_config)
        db.connect()

        assert db._connection is mock_connection
        assert db._connected is True
        mock_holo_connect_class.assert_called_once_with(sample_connection_config)
        mock_holo_connect_instance.connect.assert_called_once()

    def test_disconnect(self, sample_connection_config):
        """Test database disconnection."""
        mock_connection = Mock(spec=HoloConnect)
        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True

        db.disconnect()

        assert db._connection is None
        assert db._connected is False
        mock_connection.close.assert_called_once()

    def test_execute_without_connection(self, sample_connection_config):
        """Test execute method without connection raises error."""
        db = HoloDB(sample_connection_config)

        with pytest.raises(ConnectionError) as exc_info:
            db.execute("SELECT 1")

        assert "Database not connected" in str(exc_info.value)

    def test_execute_with_fetch_result(self, sample_connection_config):
        """Test execute method with fetch_result=True."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.fetchall.return_value = [{"id": 1, "name": "test"}]

        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True

        result = db.execute("SELECT * FROM test", fetch_result=True)

        assert result == [{"id": 1, "name": "test"}]
        mock_connection.fetchall.assert_called_once_with("SELECT * FROM test")

    def test_execute_without_fetch_result(self, sample_connection_config):
        """Test execute method with fetch_result=False."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.execute.return_value = None

        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True

        result = db.execute("INSERT INTO test VALUES (1, 'test')", fetch_result=False)

        mock_connection.execute.assert_called_once_with(
            "INSERT INTO test VALUES (1, 'test')"
        )

    # @patch("holo_search_sdk.backend.database.HoloTable")
    # def test_create_table_success(
    #     self, mock_holo_table_class, sample_connection_config, sample_table_columns
    # ):
    #     """Test successful table creation."""
    #     mock_connection = Mock(spec=HoloConnect)
    #     mock_table = Mock(spec=HoloTable)
    #     mock_holo_table_class.return_value = mock_table

    #     db = HoloDB(sample_connection_config)
    #     db._connection = mock_connection
    #     db._connected = True

    #     result = db.create_table("test_table", sample_table_columns)

    #     assert result is mock_table
    #     mock_connection.execute.assert_called_once()
    #     mock_holo_table_class.assert_called_once_with(mock_connection, "test_table")

    # def test_create_table_without_connection(
    #     self, sample_connection_config, sample_table_columns
    # ):
    #     """Test create_table without connection raises error."""
    #     db = HoloDB(sample_connection_config)

    #     with pytest.raises(ConnectionError) as exc_info:
    #         db.create_table("test_table", sample_table_columns)

    #     assert "Database not connected" in str(exc_info.value)

    # def test_create_table_exist_ok_false(
    #     self, sample_connection_config, sample_table_columns
    # ):
    #     """Test create_table with exist_ok=False when table exists."""
    #     mock_connection = Mock(spec=HoloConnect)
    #     db = HoloDB(sample_connection_config)
    #     db._connection = mock_connection
    #     db._connected = True

    #     # Mock check_table_exist to return True
    #     db.check_table_exist = Mock(return_value=True)

    #     with pytest.raises(TableError) as exc_info:
    #         db.create_table("existing_table", sample_table_columns, exist_ok=False)

    #     assert "already exists" in str(exc_info.value)

    def test_check_table_exist_true(self, sample_connection_config):
        """Test check_table_exist returns True when table exists."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.fetchone.return_value = (True,)

        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True

        result = db.check_table_exist("existing_table")

        assert result is True
        mock_connection.fetchone.assert_called_once()

    def test_check_table_exist_false(self, sample_connection_config):
        """Test check_table_exist returns False when table doesn't exist."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.fetchone.return_value = (False,)

        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True

        result = db.check_table_exist("non_existing_table")

        assert result is False

    def test_check_table_exist_query_error(self, sample_connection_config):
        """Test check_table_exist raises QueryError when fetchone returns None."""
        mock_connection = Mock(spec=HoloConnect)
        mock_connection.fetchone.return_value = None

        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True

        with pytest.raises(QueryError) as exc_info:
            db.check_table_exist("test_table")

        assert "Error executing SQL query" in str(exc_info.value)

    @patch("holo_search_sdk.backend.database.HoloTable")
    def test_open_table_success(self, mock_holo_table_class, sample_connection_config):
        """Test successful table opening."""
        mock_connection = Mock(spec=HoloConnect)
        mock_table = Mock(spec=HoloTable)
        mock_holo_table_class.return_value = mock_table

        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True
        db.check_table_exist = Mock(return_value=True)

        result = db.open_table("existing_table")

        assert result is mock_table
        db.check_table_exist.assert_called_once_with("existing_table")
        mock_holo_table_class.assert_called_once_with(mock_connection, "existing_table")

    def test_open_table_not_exist(self, sample_connection_config):
        """Test opening non-existing table raises TableError."""
        mock_connection = Mock(spec=HoloConnect)
        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True
        db.check_table_exist = Mock(return_value=False)

        with pytest.raises(TableError) as exc_info:
            db.open_table("non_existing_table")

        assert "does not exist" in str(exc_info.value)

    def test_drop_table(self, sample_connection_config):
        """Test table dropping."""
        mock_connection = Mock(spec=HoloConnect)
        db = HoloDB(sample_connection_config)
        db._connection = mock_connection
        db._connected = True

        db.drop_table("test_table")

        # Verify that execute was called with a Composed object
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args[0]
        sql_str = call_args[0].as_string()
        assert sql_str == 'DROP TABLE IF EXISTS "test_table";'


class TestHoloTable:
    """Test cases for the HoloTable class."""

    def test_holo_table_initialization(self):
        """Test HoloTable initialization."""
        mock_connection = Mock(spec=HoloConnect)
        table_name = "test_table"

        table = HoloTable(mock_connection, table_name)

        assert table._db is mock_connection
        assert table._name == table_name
        assert table._column_distance_methods == {}

    def test_get_name(self):
        """Test get_name method."""
        mock_connection = Mock(spec=HoloConnect)
        table_name = "test_table"

        table = HoloTable(mock_connection, table_name)

        assert table.get_name() == table_name

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_get_by_key_with_return_columns(self, mock_query_builder_class):
        """Test get_by_key method with specific return columns."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder.where.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")
        return_columns = ["id", "name", "vector"]

        result = table.get_by_key("id", 123, return_columns)

        assert result is mock_query_builder
        mock_query_builder_class.assert_called_once_with(mock_connection, "test_table")
        mock_query_builder.select.assert_called_once_with(return_columns)
        mock_query_builder.where.assert_called_once()

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_get_by_key_without_return_columns(self, mock_query_builder_class):
        """Test get_by_key method without specific return columns (select all)."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder.where.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")

        result = table.get_by_key("id", 123)

        assert result is mock_query_builder
        mock_query_builder_class.assert_called_once_with(mock_connection, "test_table")
        mock_query_builder.select.assert_called_once_with("*")
        mock_query_builder.where.assert_called_once()

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_get_by_key_string_value(self, mock_query_builder_class):
        """Test get_by_key method with string key value."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder.where.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")

        result = table.get_by_key("username", "test_user", ["id", "username"])

        assert result is mock_query_builder
        mock_query_builder.select.assert_called_once_with(["id", "username"])
        mock_query_builder.where.assert_called_once()

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_get_multi_by_keys_with_return_columns(self, mock_query_builder_class):
        """Test get_multi_by_keys method with specific return columns."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder.where.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")
        key_values = [1, 2, 3, 4]
        return_columns = ["id", "name", "vector"]

        result = table.get_multi_by_keys("id", key_values, return_columns)

        assert result is mock_query_builder
        mock_query_builder_class.assert_called_once_with(mock_connection, "test_table")
        mock_query_builder.select.assert_called_once_with(return_columns)
        mock_query_builder.where.assert_called_once()

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_get_multi_by_keys_without_return_columns(self, mock_query_builder_class):
        """Test get_multi_by_keys method without specific return columns (select all)."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder.where.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")
        key_values = [1, 2, 3]

        result = table.get_multi_by_keys("id", key_values)

        assert result is mock_query_builder
        mock_query_builder_class.assert_called_once_with(mock_connection, "test_table")
        mock_query_builder.select.assert_called_once_with("*")
        mock_query_builder.where.assert_called_once()

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_get_multi_by_keys_empty_list(self, mock_query_builder_class):
        """Test get_multi_by_keys method with empty key values list."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder.where.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")
        key_values = []

        result = table.get_multi_by_keys("id", key_values)

        assert result is mock_query_builder
        mock_query_builder.select.assert_called_once_with("*")
        mock_query_builder.where.assert_called_once()

    def test_insert_one_with_column_names(self):
        """Test inserting one record with column names."""
        mock_connection = Mock(spec=HoloConnect)
        table = HoloTable(mock_connection, "test_table")

        values = [1, "test", [0.1, 0.2, 0.3]]
        column_names = ["id", "content", "vector"]

        result = table.insert_one(values, column_names)

        assert result is table
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        sql_str = call_args[0][0].as_string()
        assert (
            sql_str
            == 'INSERT INTO "test_table" ("id", "content", "vector") VALUES (%s, %s, %s);'
        )
        assert call_args[0][1] == tuple(values)

    def test_insert_one_without_column_names(self):
        """Test inserting one record without column names."""
        mock_connection = Mock(spec=HoloConnect)
        table = HoloTable(mock_connection, "test_table")

        values = [1, "test"]

        result = table.insert_one(values)

        assert result is table
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        sql_str = call_args[0][0].as_string()
        assert sql_str == 'INSERT INTO "test_table" VALUES (%s, %s);'
        assert call_args[0][1] == tuple(values)

    def test_insert_multi_with_data(self):
        """Test inserting multiple records."""
        mock_connection = Mock(spec=HoloConnect)
        table = HoloTable(mock_connection, "test_table")

        values = [[1, "test1"], [2, "test2"], [3, "test3"]]
        column_names = ["id", "content"]

        result = table.insert_multi(values, column_names)

        assert result is table
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        sql_str = call_args[0][0].as_string()
        assert (
            sql_str
            == 'INSERT INTO "test_table" ("id", "content") VALUES (%s, %s), (%s, %s), (%s, %s);'
        )
        # Check that all values are flattened in the tuple
        expected_params = (1, "test1", 2, "test2", 3, "test3")
        assert call_args[0][1] == expected_params

    def test_insert_multi_empty_values(self):
        """Test inserting empty list returns table without executing."""
        mock_connection = Mock(spec=HoloConnect)
        table = HoloTable(mock_connection, "test_table")

        result = table.insert_multi([])

        assert result is table
        mock_connection.execute.assert_not_called()

    def test_set_vector_index(self):
        """Test setting a vector index."""
        mock_connection = Mock(spec=HoloConnect)
        table = HoloTable(mock_connection, "test_table")

        result = table.set_vector_index(
            column="vector_col",
            distance_method="Euclidean",
            base_quantization_type="rabitq",
            max_degree=64,
            ef_construction=400,
        )

        assert result is table
        assert table._column_distance_methods["vector_col"] == "Euclidean"
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        sql_str = call_args[0][0].as_string()
        expected_str = """CALL set_table_property('test_table', 'vectors', '{"vector_col": {"algorithm": "HGraph", "distance_method": "Euclidean", "builder_params": {"max_degree": 64, "ef_construction": 400, "base_quantization_type": "rabitq", "use_reorder": false, "precise_quantization_type": "fp32", "precise_io_type": "block_memory_io", "max_total_size_to_merge_mb": 4096, "build_thread_count": 16}}}');"""
        assert sql_str == expected_str

    def test_set_vector_indexes(self):
        """Test setting multiple vector indexes."""
        mock_connection = Mock(spec=HoloConnect)
        table = HoloTable(mock_connection, "test_table")

        column_configs = {
            "vector1": {
                "distance_method": "Euclidean",
                "base_quantization_type": "rabitq",
                "max_degree": 32,
            },
            "vector2": {
                "distance_method": "Cosine",
                "base_quantization_type": "rabitq",
                "ef_construction": 300,
            },
        }

        result = table.set_vector_indexes(column_configs)

        assert result is table
        assert table._column_distance_methods["vector1"] == "Euclidean"
        assert table._column_distance_methods["vector2"] == "Cosine"
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        sql_str = call_args[0][0].as_string()
        expected_str = """
            CALL set_table_property(
                'test_table',
                'vectors',
                '{"vector1": {"algorithm": "HGraph", "distance_method": "Euclidean", "builder_params": {"max_degree": 32, "ef_construction": 400, "base_quantization_type": "rabitq", "use_reorder": false, "precise_quantization_type": "fp32", "precise_io_type": "block_memory_io", "max_total_size_to_merge_mb": 4096, "build_thread_count": 16}}, "vector2": {"algorithm": "HGraph", "distance_method": "Cosine", "builder_params": {"max_degree": 64, "ef_construction": 300, "base_quantization_type": "rabitq", "use_reorder": false, "precise_quantization_type": "fp32", "precise_io_type": "block_memory_io", "max_total_size_to_merge_mb": 4096, "build_thread_count": 16}}}');
            """
        assert sql_str == expected_str

    def test_delete_vector_indexes(self):
        """Test deleting all vector indexes."""
        mock_connection = Mock(spec=HoloConnect)
        table = HoloTable(mock_connection, "test_table")
        table._column_distance_methods = {"vector1": "Euclidean", "vector2": "Cosine"}

        result = table.delete_vector_indexes()

        assert result is table
        assert table._column_distance_methods == {}
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        sql_str = call_args[0][0].as_string()
        expected_str = """
        CALL set_table_property(
            'test_table',
            'vectors',
            '{}');
        """
        assert sql_str == expected_str

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_search_vector_with_distance_method(self, mock_query_builder_class):
        """Test vector search with explicit distance method."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")
        vector = [0.1, 0.2, 0.3]

        result = table.search_vector(vector, "vector_col", distance_method="Euclidean")

        assert result is mock_query_builder
        mock_query_builder_class.assert_called_once_with(mock_connection, "test_table")
        mock_query_builder.select.assert_called_once()

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_search_vector_with_cached_distance_method(self, mock_query_builder_class):
        """Test vector search with cached distance method."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")
        table._column_distance_methods["vector_col"] = "Cosine"
        vector = [0.1, 0.2, 0.3]

        result = table.search_vector(vector, "vector_col")

        assert result is mock_query_builder
        mock_query_builder.select.assert_called_once()

    def test_search_vector_no_distance_method(self):
        """Test vector search without distance method raises SqlError."""
        mock_connection = Mock(spec=HoloConnect)
        table = HoloTable(mock_connection, "test_table")
        vector = [0.1, 0.2, 0.3]

        with pytest.raises(SqlError) as exc_info:
            table.search_vector(vector, "vector_col")

        assert "Distance method must be set" in str(exc_info.value)

    @patch("holo_search_sdk.backend.table.QueryBuilder")
    def test_search_vector_with_output_name(self, mock_query_builder_class):
        """Test vector search with custom output name."""
        mock_connection = Mock(spec=HoloConnect)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder_class.return_value = mock_query_builder

        table = HoloTable(mock_connection, "test_table")
        vector = [0.1, 0.2, 0.3]

        result = table.search_vector(
            vector, "vector_col", output_name="similarity", distance_method="Euclidean"
        )

        assert result is mock_query_builder
        # Check that select was called with a tuple (for aliasing in psycopg3)
        call_args = mock_query_builder.select.call_args[0][0]
        assert isinstance(call_args, tuple)


class TestBackendIntegration:
    """Integration tests for backend components."""

    @patch("holo_search_sdk.backend.database.HoloConnect")
    @patch("holo_search_sdk.backend.database.HoloTable")
    def test_full_workflow(
        self, mock_holo_table_class, mock_holo_connect_class, sample_connection_config
    ):
        """Test a complete workflow from connection to table operations."""
        # Setup mocks
        mock_connection = Mock(spec=HoloConnect)
        mock_holo_connect_instance = Mock()
        mock_holo_connect_instance.connect.return_value = mock_connection
        mock_holo_connect_class.return_value = mock_holo_connect_instance

        mock_table = Mock(spec=HoloTable)
        mock_holo_table_class.return_value = mock_table

        # Create and connect database
        db = HoloDB(sample_connection_config)
        db.connect()

        # Mock check_table_exist to return True (table exists)
        mock_connection.fetchone.return_value = (True,)

        # Open existing table instead of creating
        table = db.open_table("test_table")

        # Verify the workflow
        assert db._connected is True
        assert db._connection is mock_connection
        assert table is mock_table

        mock_holo_connect_class.assert_called_once_with(sample_connection_config)
        mock_holo_connect_instance.connect.assert_called_once()
        mock_connection.fetchone.assert_called_once()
        mock_holo_table_class.assert_called_once_with(mock_connection, "test_table")

    def test_error_propagation(self, sample_connection_config):
        """Test that errors are properly propagated through the backend layers."""
        db = HoloDB(sample_connection_config)

        # Test ConnectionError propagation
        with pytest.raises(ConnectionError):
            db.execute("SELECT 1")

        with pytest.raises(ConnectionError):
            db.check_table_exist("test")

        with pytest.raises(ConnectionError):
            db.open_table("test")

        with pytest.raises(ConnectionError):
            db.drop_table("test")
