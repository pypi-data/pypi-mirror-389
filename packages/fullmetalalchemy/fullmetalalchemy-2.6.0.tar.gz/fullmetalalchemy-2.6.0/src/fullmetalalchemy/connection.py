"""
Connection-based operations for transaction control.

This module provides connection-level operations that use autoload_with=connection
to ensure transaction visibility. This is critical for seeing uncommitted schema
changes within the same transaction.

Unlike session-based operations, these functions work directly with Connection
objects from engine.connect() or engine.begin(), providing finer control over
transactions.

Examples
--------
>>> import fullmetalalchemy as fa
>>>
>>> engine = fa.create_engine('sqlite:///data.db')
>>> with engine.begin() as conn:
...     # Insert, update, delete in same transaction
...     fa.connection.insert_records_connection(table, records, conn)
...     fa.connection.update_records_connection(table, updated_records, conn)
...     # Auto-commits on exit
"""

import typing as _t

import sqlalchemy as _sa
import sqlalchemy.engine as _sa_engine

import fullmetalalchemy.features as _features
import fullmetalalchemy.types as _types


def insert_records_connection(
    table: _t.Union[_sa.Table, str],
    records: _t.Sequence[_types.Record],
    connection: _sa_engine.Connection,
    schema: _t.Optional[str] = None,
) -> None:
    """
    Insert records using a connection for transaction control.

    This is useful when you need to insert within an existing transaction
    and want to use the connection object directly rather than a session.

    Parameters
    ----------
    table : Union[Table, str]
        Table object or name
    records : Sequence[Record]
        Records to insert
    connection : Connection
        SQLAlchemy connection (from engine.connect() or engine.begin())
    schema : Optional[str]
        Schema name

    Examples
    --------
    >>> import fullmetalalchemy as fa
    >>> engine = fa.create_engine('sqlite:///test.db')
    >>> with engine.begin() as conn:
    ...     fa.connection.insert_records_connection('users', records, conn)
    """
    # If table is string, need to load it with autoload_with for transaction visibility
    if isinstance(table, str):
        metadata = _sa.MetaData(schema=schema)
        # Use autoload_with=connection to see uncommitted changes
        table = _sa.Table(table, metadata, autoload_with=connection, schema=schema)

    # Build insert statement
    stmt = table.insert()
    connection.execute(stmt, records)


def update_records_connection(
    table: _t.Union[_sa.Table, str],
    records: _t.Sequence[_types.Record],
    connection: _sa_engine.Connection,
    match_column_names: _t.Optional[_t.Sequence[str]] = None,
    schema: _t.Optional[str] = None,
) -> None:
    """
    Update records using a connection with autoload_with support.

    This is critical for seeing transaction state - uses autoload_with=connection
    so that schema changes within the same transaction are visible.

    Parameters
    ----------
    table : Union[Table, str]
        Table object or name
    records : Sequence[Record]
        Records to update (must include match columns)
    connection : Connection
        SQLAlchemy connection
    match_column_names : Optional[Sequence[str]]
        Columns to match on (defaults to primary key)
    schema : Optional[str]
        Schema name

    Examples
    --------
    >>> import fullmetalalchemy as fa
    >>> engine = fa.create_engine('sqlite:///test.db')
    >>> with engine.begin() as conn:
    ...     fa.connection.update_records_connection(
    ...         'users',
    ...         [{'id': 1, 'name': 'Alice'}],
    ...         conn
    ...     )
    """
    # CRITICAL: Use autoload_with=connection to see uncommitted changes
    if isinstance(table, str):
        metadata = _sa.MetaData(schema=schema)
        table = _sa.Table(table, metadata, autoload_with=connection, schema=schema)

    # Determine match columns (primary key if not specified)
    if match_column_names is None:
        pk_cols = _features.primary_key_names(table)
        if not pk_cols:
            raise ValueError("Table has no primary key, must specify match_column_names")
        match_column_names = pk_cols

    # Build updates for each record
    for record in records:
        # Build WHERE clause based on match columns
        where_clause = [table.c[col] == record[col] for col in match_column_names]
        # Build SET clause for non-match columns
        update_values = {col: val for col, val in record.items() if col not in match_column_names}
        if update_values:  # Only update if there are values to set
            stmt = table.update().where(_sa.and_(*where_clause)).values(**update_values)
            connection.execute(stmt)


def delete_records_connection(
    table: _t.Union[_sa.Table, str],
    connection: _sa_engine.Connection,
    column_name: _t.Optional[str] = None,
    values: _t.Optional[_t.Sequence[_t.Any]] = None,
    records: _t.Optional[_t.Sequence[_types.Record]] = None,
    primary_key_values: _t.Optional[_t.Sequence[_t.Union[_t.Any, _t.Tuple[_t.Any, ...]]]] = None,
    schema: _t.Optional[str] = None,
) -> None:
    """
    Delete records using a connection.

    Supports multiple deletion patterns:
    - By column values: column_name + values
    - By record matching: records
    - By primary key: primary_key_values (single or composite)

    Parameters
    ----------
    table : Union[Table, str]
        Table object or name
    connection : Connection
        SQLAlchemy connection
    column_name : Optional[str]
        Column name for value-based deletion
    values : Optional[Sequence[Any]]
        Values to match in column_name
    records : Optional[Sequence[Record]]
        Full records to match
    primary_key_values : Optional[Sequence[Union[Any, Tuple[Any, ...]]]]
        Primary key values (single values or tuples for composite)
    schema : Optional[str]
        Schema name

    Examples
    --------
    >>> import fullmetalalchemy as fa
    >>> engine = fa.create_engine('sqlite:///test.db')
    >>> with engine.begin() as conn:
    ...     # Delete by single PK
    ...     fa.connection.delete_records_connection(
    ...         'users', conn, primary_key_values=[1, 2, 3]
    ...     )
    ...     # Delete by composite PK
    ...     fa.connection.delete_records_connection(
    ...         'memberships',
    ...         conn,
    ...         primary_key_values=[(1, 10), (2, 20)]
    ...     )
    """
    if isinstance(table, str):
        metadata = _sa.MetaData(schema=schema)
        table = _sa.Table(table, metadata, autoload_with=connection, schema=schema)

    # Pattern 1: By column values
    if column_name and values:
        stmt = table.delete().where(table.c[column_name].in_(values))
        connection.execute(stmt)

    # Pattern 2: By primary key values
    elif primary_key_values is not None:
        pk_names = _features.primary_key_names(table)
        if not pk_names:
            raise ValueError("Table has no primary key")

        if len(pk_names) == 1:  # Single PK
            stmt = table.delete().where(table.c[pk_names[0]].in_(primary_key_values))
        else:  # Composite PK - values should be tuples
            or_clauses = []
            for pk_tuple in primary_key_values:
                and_clauses = [
                    table.c[pk_name] == pk_val for pk_name, pk_val in zip(pk_names, pk_tuple)
                ]
                or_clauses.append(_sa.and_(*and_clauses))
            stmt = table.delete().where(_sa.or_(*or_clauses))
        connection.execute(stmt)

    # Pattern 3: By record matching
    elif records:
        for record in records:
            where_clause = [table.c[key] == value for key, value in record.items()]
            stmt = table.delete().where(_sa.and_(*where_clause))
            connection.execute(stmt)

    else:
        raise ValueError(
            "Must provide deletion criteria: column_name+values, records, or primary_key_values"
        )
