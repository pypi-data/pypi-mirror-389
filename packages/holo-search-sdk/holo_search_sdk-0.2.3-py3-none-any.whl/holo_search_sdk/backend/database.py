"""
Hologres backend implementation for Holo Search SDK.

Provides database backend implementations and factory functions.
"""

from typing import Optional

from psycopg import sql as psql
from psycopg.abc import Query

from ..exceptions import ConnectionError, QueryError, TableError
from ..types import ConnectionConfig
from .connection import HoloConnect
from .table import HoloTable


class HoloDB:
    """
    Hologres backend implementation.

    Provides database backend implementations and factory functions.
    """

    def __init__(self, config: ConnectionConfig):
        """Initialize the Hologres database backend."""
        self._connection: Optional[HoloConnect] = None
        self._config: ConnectionConfig = config
        self._connected: bool = False

    def connect(self) -> None:
        """Establish connection to Hologres database."""
        self._connection = HoloConnect(self._config).connect()
        self._connected = True

    def disconnect(self) -> None:
        """Close connection to Hologres database."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self._connected = False

    def execute(self, sql: Query, fetch_result: bool = False):
        """
        Execute a SQL query.

        Args:
            sql: SQL query to execute
            fetch_result: Whether to fetch the result of the query
        """
        if not self._connected or not self._connection:
            raise ConnectionError("Database not connected. Call connect() first.")
        if fetch_result:
            return self._connection.fetchall(sql)
        else:
            return self._connection.execute(sql)

    # def create_table(
    #     self,
    #     table_name: str,
    #     columns: Mapping[str, Union[str, Tuple[str, str]]],
    #     exist_ok: bool = True,
    # ) -> HoloTable:
    #     """
    #     Create a new table in Hologres database.

    #     Args:
    #         table_name: Table name
    #         columns (Dict[str, Union[str, Tuple[str, str]]]): Dictionary of column definitions
    #             - Dictionary key is the column name
    #             - Dictionary value can be one of the following formats:
    #                 * str: Column type only, e.g., 'VARCHAR(255)', 'TEXT', 'INTEGER'
    #                 * Tuple[str, str]: (column_type, constraints), e.g., ('VARCHAR(255)', 'PRIMARY KEY')
    #         exist_ok: If True, do not raise an error if the table already exists.
    #     """
    #     if not self._connected or not self._connection:
    #         raise ConnectionError("Database not connected. Call connect() first.")
    #     if not exist_ok and self.check_table_exist(table_name):
    #         raise TableError(f"Table {table_name} already exists")
    #     sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
    #     for column_name, column_config in columns.items():
    #         if isinstance(column_config, str):
    #             sql += f"{column_name} {column_config}, "
    #         else:
    #             sql += f"{column_name} {column_config[0]} {column_config[1]}, "
    #     sql = sql[:-2] + ");"
    #     self._connection.execute(sql)
    #     return HoloTable(self._connection, table_name)

    def check_table_exist(self, table_name: str) -> bool:
        """
        Check if the table exists.

        Args:
            table_name (str): Name of the table.
        """
        if not self._connected or not self._connection:
            raise ConnectionError("Database not connected. Call connect() first.")

        sql = psql.SQL(
            """
        SELECT EXISTS(
            SELECT 1 
            FROM pg_tables 
            WHERE schemaname = {} 
            AND tablename = {}
        );
        """
        ).format(psql.Literal(self._config.schema), psql.Literal(table_name))
        res = self._connection.fetchone(sql)
        if not res:
            raise QueryError("Error executing SQL query")
        elif res[0] is True:
            return True
        elif res[0] is False:
            return False
        else:
            raise QueryError("Unexpected result from query")

    def open_table(self, table_name: str) -> HoloTable:
        """
        Open an existing table in Hologres database.

        Args:
            table_name: Table name

        Returns:
            HoloTable: Table instance
        """
        if not self._connected or not self._connection:
            raise ConnectionError("Database not connected. Call connect() first.")

        is_exist = self.check_table_exist(table_name)
        if is_exist:
            return HoloTable(self._connection, table_name)
        else:
            raise TableError(f"Table {table_name} does not exist")

    def drop_table(self, table_name: str) -> None:
        """
        Drop a table if it exists.

        Args:
            table_name: Table name
        """
        if not self._connected or not self._connection:
            raise ConnectionError("Database not connected. Call connect() first.")

        self._connection.execute(
            psql.SQL("DROP TABLE IF EXISTS {};").format(psql.Identifier(table_name))
        )
