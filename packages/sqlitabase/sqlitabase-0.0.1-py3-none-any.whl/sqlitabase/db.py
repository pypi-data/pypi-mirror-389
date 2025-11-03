from __future__ import annotations

import os
import sqlite3
from enum import Enum
from typing import Any, Iterator

from typing_extensions import Self


QueryParams = tuple[Any, ...] | dict[str, Any] | None


class RowStyle(str, Enum):
    DICT = 'dict'
    TUPLE = 'tuple'


class FetchMode(str, Enum):
    COLUMN = 'column'
    KEY_PAIR = 'key_pair'
    KEY_PAIR_LIST = 'key_pair_list'
    GROUP = 'group'
    GROUP_COLUMN = 'group_column'


class QueryResult:
    """An iterable container for query results.
    This object is an iterator and can be used in a `for` loop.
    """

    def __init__(
        self,
        cursor: sqlite3.Cursor,
        row_style: RowStyle = RowStyle.DICT,
    ) -> None:
        self._cursor = cursor
        self._row_style = row_style

    def __iter__(
        self,
    ) -> Iterator[dict[str, Any] | tuple[Any, ...]]:
        """Allows for direct iteration over the results, yielding rows in the
        initial 'style' (dict or tuple).
        """
        if self._row_style == RowStyle.DICT:
            self._cursor.row_factory = sqlite3.Row
        else:
            self._cursor.row_factory = None
        yield from self._cursor

    def fetch(self, style: RowStyle | None = None) -> dict[str, Any] | tuple[Any, ...] | None:
        """Fetches the next row from the result set.

        Args:
            style: Override the default row style for this fetch.
                   RowStyle.DICT for dictionary, RowStyle.TUPLE for tuple.
                   If None, uses the default from db.query().

        Returns:
            The next row as a dict or tuple, or None if no more rows.

        Raises:
            ValueError: If an invalid style is provided.

        """
        current_factory = self._cursor.row_factory

        if style == RowStyle.DICT:
            self._cursor.row_factory = sqlite3.Row
        elif style == RowStyle.TUPLE:
            self._cursor.row_factory = None
        elif style is not None:
            msg = 'Invalid style. Use RowStyle.DICT or RowStyle.TUPLE.'
            raise ValueError(msg)

        result = self._cursor.fetchone()

        # Convert sqlite3.Row to dict if needed
        if result is not None and isinstance(result, sqlite3.Row):
            result = dict(result)

        self._cursor.row_factory = current_factory

        return result

    def fetch_all(
        self,
        mode: FetchMode | None = None,
        key_column: str | int = 0,
        value_column: str | int = 1,
    ) -> list[dict[str, Any] | tuple[Any, ...]] | dict[Any, Any]:
        """Fetches all remaining rows from the result set based on a specific mode.

        Args:
            mode: How to fetch the data.
                  - FetchMode.COLUMN: List of values from a single column.
                  - FetchMode.KEY_PAIR: Dictionary mapping 1st col to 2nd col.
                  - FetchMode.KEY_PAIR_LIST: Dictionary mapping 1st col to list of remaining cols.
                  - FetchMode.GROUP: Dictionary grouping by 1st col, values are list of rows.
                  - FetchMode.GROUP_COLUMN: Dictionary grouping by 1st col, values are list of 2nd col.
                  If None, returns list of rows in default style.
            key_column: The column to use as key. Can be column name (str) or index (int).
            value_column: The column to use as value. Can be column name (str) or index (int).

        Returns:
            Data fetched in the specified mode.

        Raises:
            ValueError: If an invalid mode or column specification is provided.
            TypeError: If column access by name is attempted on tuple rows without column names.

        """
        raw_results = self._cursor.fetchall()

        # Convert sqlite3.Row objects to dicts if in DICT mode
        if raw_results and isinstance(raw_results[0], sqlite3.Row):
            raw_results = [dict(row) for row in raw_results]

        if not raw_results:
            return (
                []
                if mode
                not in [
                    FetchMode.KEY_PAIR,
                    FetchMode.KEY_PAIR_LIST,
                    FetchMode.GROUP,
                    FetchMode.GROUP_COLUMN,
                ]
                else {}
            )

        if mode is None:
            return list(raw_results)

        column_names = [d[0] for d in self._cursor.description] if self._cursor.description else []

        def get_value(row, col_id_or_name):
            if isinstance(col_id_or_name, int):
                return row[col_id_or_name]
            if isinstance(row, dict):
                return row.get(col_id_or_name)
            if column_names:
                try:
                    return row[column_names.index(col_id_or_name)]
                except ValueError as e:
                    msg = f"Column '{col_id_or_name}' not found."
                    raise ValueError(msg) from e
            msg = 'Cannot access column by name if row is tuple and no column names available.'
            raise TypeError(msg)

        if mode == FetchMode.COLUMN:
            return [get_value(row, key_column) for row in raw_results]

        if mode == FetchMode.KEY_PAIR:
            return {get_value(row, key_column): get_value(row, value_column) for row in raw_results}

        if mode == FetchMode.KEY_PAIR_LIST:
            result = {}
            for row in raw_results:
                key = get_value(row, key_column)
                if isinstance(row, dict):
                    value = {k: v for k, v in row.items() if k != key_column}
                else:
                    value = tuple(r for i, r in enumerate(row) if i != key_column)
                result[key] = value
            return result

        if mode == FetchMode.GROUP:
            result = {}
            for row in raw_results:
                key = get_value(row, key_column)
                if isinstance(row, dict):
                    grouped_item = {k: v for k, v in row.items() if k != key_column}
                else:
                    grouped_item = tuple(r for i, r in enumerate(row) if i != key_column)
                result.setdefault(key, []).append(grouped_item)
            return result

        if mode == FetchMode.GROUP_COLUMN:
            result = {}
            for row in raw_results:
                key = get_value(row, key_column)
                value = get_value(row, value_column)
                result.setdefault(key, []).append(value)
            return result

        msg = f'Unknown fetch mode: {mode}. Allowed: {", ".join(m.value for m in FetchMode)}'
        raise ValueError(msg)

    @property
    def row_count(self) -> int:
        """Returns the number of rows affected by the query."""
        return self._cursor.rowcount


class DBHelper:
    """A robust helper for SQLite operations, supporting both managed
    (with statement) and unmanaged (manual) connection modes,
    and configurable auto-commit.
    """

    def __init__(self, db_path: str | None = None, autocommit: bool = False) -> None:
        self.db_path = db_path or os.getenv('SQLITE_DB_PATH')
        if not self.db_path:
            msg = 'No database path found. Pass it to the constructor or set SQLITE_DB_PATH in your environment.'
            raise ValueError(msg)
        self._connection: sqlite3.Connection | None = None
        self._autocommit = autocommit

    def _get_connection(self) -> sqlite3.Connection:
        """Lazily creates and returns the database connection."""
        if self._connection is None:
            if not self.db_path:
                msg = 'Database path is required.'
                raise ValueError(msg)
            # Set isolation_level to None for autocommit, otherwise default
            isolation_level = None if self._autocommit else 'DEFERRED'
            self._connection = sqlite3.connect(self.db_path, isolation_level=isolation_level)
        return self._connection

    def __enter__(self) -> Self:
        """Enters a managed block, ensuring a connection is active."""
        self._get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exits the managed block, committing or rolling back and closing."""
        if self._connection:
            if not self._autocommit:
                if exc_type:
                    self._connection.rollback()
                else:
                    self._connection.commit()
            self._connection.close()
            self._connection = None

    def commit(self) -> None:
        """Manually commits the current transaction. Has no effect in autocommit mode."""
        conn = self._get_connection()
        if not self._autocommit:
            conn.commit()

    def rollback(self) -> None:
        """Manually rolls back the current transaction. Has no effect in autocommit mode."""
        conn = self._get_connection()
        if not self._autocommit:
            conn.rollback()

    def close(self) -> None:
        """Manually closes the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def query(
        self,
        query: str,
        params: QueryParams = None,
        style: RowStyle = RowStyle.DICT,
    ) -> QueryResult:
        """Executes a query and returns an iterable QueryResult.

        Args:
            query: The SQL to execute.
            params: Parameters to bind (tuple or dict).
            style: RowStyle.DICT for dictionary rows, RowStyle.TUPLE for tuple rows.

        Returns:
            An iterable object for fetching results.

        Raises:
            ValueError: If an invalid style is provided.

        """
        if style not in [RowStyle.DICT, RowStyle.TUPLE]:
            msg = 'Invalid style. Use RowStyle.DICT or RowStyle.TUPLE.'
            raise ValueError(msg)

        conn = self._get_connection()
        cursor = conn.cursor()

        # Set row factory based on style
        if style == RowStyle.DICT:
            cursor.row_factory = sqlite3.Row
        else:
            cursor.row_factory = None

        # Handle different parameter styles
        if params is None:
            cursor.execute(query)
        elif isinstance(params, dict):
            cursor.execute(query, params)
        else:
            cursor.execute(query, params)

        # For non-SELECT queries in autocommit mode
        if self._autocommit and cursor.description is None:
            conn.commit()

        return QueryResult(cursor, style)

    def execute_many(self, query: str, param_list: list[QueryParams]) -> int:
        """Executes a single query multiple times with different parameter sets.
        This is typically much faster for bulk operations than individual queries.

        Args:
            query: The SQL query (e.g., INSERT INTO users (name, email) VALUES (?, ?)).
            param_list: A list of parameter sets, where each set is a tuple or dictionary.

        Returns:
            The total number of rows affected by all executions.

        """
        if not param_list:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, param_list)

        if self._autocommit:
            conn.commit()

        return cursor.rowcount
