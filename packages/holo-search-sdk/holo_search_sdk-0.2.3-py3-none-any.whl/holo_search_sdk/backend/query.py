"""
Query module for Holo Search SDK.

Provides query builder classes for different types of searches.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from psycopg import sql as psql
from typing_extensions import LiteralString

from ..exceptions import SqlError
from .connection import HoloConnect


class QueryBuilder:
    """
    Base query builder class for different types of searches.
    """

    def __init__(self, connection: HoloConnect, table_name: str):
        """
        Initialize base query.
        """
        self._connection: HoloConnect = connection
        self._table_name: str = table_name
        self._limit: Optional[int] = None
        self._offset: int = 0
        self._filters: List[psql.Composable] = []
        self._select_fields: list[Tuple[psql.Composable, Optional[psql.Composable]]] = (
            []
        )
        self._order_by: Optional[psql.Composable] = None
        self._group_by: Optional[psql.Composable] = None
        self._sort_order: str = "desc"

    def limit(self, count: int) -> "QueryBuilder":
        """
        Limit the number of results.

        Args:
            count: Maximum number of results

        Returns:
            Self for method chaining
        """
        self._limit = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        """
        Skip a number of results.

        Args:
            count: Number of results to skip

        Returns:
            Self for method chaining
        """
        self._offset = count
        return self

    def where(self, filter: Union[LiteralString, psql.Composable]) -> "QueryBuilder":
        """
        Add filter conditions.

        Args:
            *filters:

        Returns:
            Self for method chaining
        """
        if isinstance(filter, psql.Composable):
            self._filters.append(filter)
        else:
            self._filters.append(psql.SQL(filter))
        return self

    def select(
        self,
        columns: Union[
            LiteralString,
            psql.Composable,
            List[
                Union[
                    LiteralString,
                    psql.Composable,
                    Tuple[
                        Union[LiteralString, psql.Composable],
                        Optional[Union[LiteralString, psql.Composable]],
                    ],
                ]
            ],
            Dict[LiteralString, Optional[Union[LiteralString, psql.Composable]]],
            Tuple[
                Union[LiteralString, psql.Composable],
                Optional[Union[LiteralString, psql.Composable]],
            ],
        ],
    ) -> "QueryBuilder":
        """
        Select specific fields to return.

        Args:
            columns: Column name or list of column names or dictionary mapping column names to aliases to return.

        Returns:
            Self for method chaining
        """
        if isinstance(columns, list):
            for column in columns:
                if isinstance(column, Tuple):
                    name = (
                        psql.SQL(column[0]) if isinstance(column[0], str) else column[0]
                    )
                    alias = (
                        psql.SQL(column[1]) if isinstance(column[1], str) else column[1]
                    )
                    self._select_fields.append((name, alias))
                elif isinstance(column, psql.Composable):
                    self._select_fields.append((column, None))
                else:
                    self._select_fields.append((psql.SQL(column), None))
        elif isinstance(columns, Dict):
            for column, alias in columns.items():
                transferred_alias = (
                    alias
                    if alias is None or isinstance(alias, psql.Composable)
                    else psql.SQL(alias)
                )
                self._select_fields.append((psql.SQL(column), transferred_alias))
        elif isinstance(columns, Tuple):
            name = psql.SQL(columns[0]) if isinstance(columns[0], str) else columns[0]
            alias = psql.SQL(columns[1]) if isinstance(columns[1], str) else columns[1]
            self._select_fields.append((name, alias))
        elif isinstance(columns, psql.Composable):
            self._select_fields.append((columns, None))
        else:
            self._select_fields.append((psql.SQL(columns), None))
        return self

    def order_by(
        self, column: Union[LiteralString, psql.Composable], order: str = "desc"
    ) -> "QueryBuilder":
        """
        Order results by a column.

        Args:
            column: Column name to order by
            order: Sort order ("asc" or "desc")

        Returns:
            Self for method chaining
        """
        if isinstance(column, psql.Composable):
            self._order_by = column
        else:
            self._order_by = psql.SQL(column)
        self._sort_order = order
        return self

    def group_by(self, column: Union[LiteralString, psql.Composable]) -> "QueryBuilder":
        """
        Group results by a column.

        Args:
            column: Column name to group by

        Returns:
            Self for method chaining
        """
        if isinstance(column, psql.Composable):
            self._group_by = column
        else:
            self._group_by = psql.SQL(column)
        return self

    def _generate_sql(self):
        """
        Generate SQL query.
        """
        if len(self._select_fields) == 0:
            raise SqlError("Select fields is not set")
        select_list: list[psql.Composable] = []
        for column, alias in self._select_fields:
            if alias:
                select_list.append(column + psql.SQL(" AS ") + alias)
            else:
                select_list.append(column)
        sql = psql.Composed([psql.SQL("SELECT "), psql.SQL(", ").join(select_list)])

        sql += psql.SQL(" FROM {}").format(psql.Identifier(self._table_name))
        if len(self._filters) > 0:
            sql += psql.Composed(
                [psql.SQL(" WHERE "), psql.SQL(" AND ").join(self._filters)]
            )
        if self._group_by is not None:
            sql += psql.SQL(" GROUP BY ") + self._group_by
        if self._order_by is not None:
            sql += psql.SQL(" ORDER BY ") + self._order_by
            if self._sort_order.upper() == "DESC":
                sql += psql.SQL(" DESC")
            else:
                sql += psql.SQL(" ASC")
        if self._limit is not None:
            sql += psql.SQL(" LIMIT {}").format(self._limit)
        sql += psql.SQL(" OFFSET {};").format(self._offset)
        return sql

    def submit(self):
        """Execute the query without return results."""
        sql = self._generate_sql()
        self._connection.execute(sql)

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        """Execute the query and return one result."""
        sql = self._generate_sql()
        return self._connection.fetchone(sql)

    def fetchall(self) -> List[Tuple[Any, ...]]:
        """Execute the query and return all results."""
        sql = self._generate_sql()
        return self._connection.fetchall(sql)

    def fetchmany(self, size: int = 0) -> List[Tuple[Any, ...]]:
        """
        Execute the query and return a number of results.

        Args:
            size: Number of results to return.
        """
        sql = self._generate_sql()
        return self._connection.fetchmany(sql, params=None, size=size)
