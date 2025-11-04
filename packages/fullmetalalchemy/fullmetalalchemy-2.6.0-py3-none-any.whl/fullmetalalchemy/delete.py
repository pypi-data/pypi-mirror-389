"""
Functions for deleting records from SQL tables.
"""

import typing as _t

import sqlalchemy as _sa
import sqlalchemy.engine as _sa_engine

import fullmetalalchemy.exceptions as _ex
import fullmetalalchemy.features as _features
import fullmetalalchemy.session as _session

# Re-export session functions for backward compatibility
delete_records_session = _session.delete_records
delete_record_by_values_session = _session.delete_record_by_values
delete_records_by_values_session = _session.delete_records_by_values
delete_all_records_session = _session.delete_all_records
_build_delete_from_record = _session._build_delete_from_record


def delete_records(
    table: _t.Union[_sa.Table, str],
    column_name: str,
    values: _t.Sequence[_t.Any],
    engine: _t.Optional[_sa_engine.Engine] = None,
) -> None:
    """
    Delete records from SQL table that match passed values in column.

    Parameters
    ----------
    table : sa.Table | str
        SqlAlchemy Table or name of SQL table
    column_name : str
        SQL table column name to match values
    values : Sequence
        values to match in SQL table column
    engine : SqlAlchemy Engine
        SqlAlchemy connection engine

    Returns
    -------
    None

    Example
    -------
    >>> import fullmetalalchemy as fa

    >>> engine, table = fa.get_engine_table('sqlite:///data/test.db', 'xy')
    >>> fa.select.select_records_all(table)
    [{'id': 1, 'x': 1, 'y': 2},
     {'id': 2, 'x': 2, 'y': 4},
     {'id': 3, 'x': 4, 'y': 8},
     {'id': 4, 'x': 8, 'y': 11}]

    >>> fa.delete.delete_records(table, 'id', [1])
    >>> fa.select.select_records_all(table)
    [{'id': 2, 'x': 2, 'y': 4},
     {'id': 3, 'x': 4, 'y': 8},
     {'id': 4, 'x': 8, 'y': 11}]

    See Also
    --------
    fullmetalalchemy.delete.delete_records_by_values
    """
    table, engine = _ex.convert_table_engine(table, engine)
    session = _features.get_session(engine)
    try:
        _session.delete_records(table, column_name, values, session)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def delete_records_by_values(
    table: _t.Union[_sa.Table, str],
    records: _t.Sequence[_t.Dict[str, _t.Any]],
    engine: _t.Optional[_sa.engine.Engine] = None,
) -> None:
    """
    Deletes records from a SQL table that match the passed records.

    Parameters
    ----------
    table : sa.Table | str
        SqlAlchemy Table or table name
    records : Sequence[Dict]
        records to match in SQL table
    engine : Optional[sa.engine.Engine]
        SqlAlchemy connection engine. If not given, it will try to obtain one from the passed table.

    Returns
    -------
    None

    Example
    -------
    >>> import sqlalchemize as sz

    >>> engine, table = sz.get_engine_table('sqlite:///data/test.db', 'xy')
    >>> sz.select.select_records_all(table)
    [{'id': 1, 'x': 1, 'y': 2},
     {'id': 2, 'x': 2, 'y': 4},
     {'id': 3, 'x': 4, 'y': 8},
     {'id': 4, 'x': 8, 'y': 11}]

    >>> sz.delete.delete_records_by_values(table, [{'id': 3}, {'x': 2}], engine)
    >>> sz.select.select_records_all(table)
    [{'id': 1, 'x': 1, 'y': 2},
     {'id': 4, 'x': 8, 'y': 11}]
    """
    table, engine = _ex.convert_table_engine(table, engine)
    session = _features.get_session(engine)
    try:
        _session.delete_records_by_values(table, records, session)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def delete_all_records(
    table: _t.Union[_sa.Table, str], engine: _t.Optional[_sa_engine.Engine] = None
) -> None:
    """
    Delete all records from a table.

    Parameters
    ----------
    table : Union[sqlalchemy.Table, str]
        The table to delete records from.
    engine : Optional[sqlalchemy.engine.Engine]
        The engine to use. If `None`, use default engine.

    Returns
    -------
    None

    Raises
    ------
    fullmetalalchemy.exceptions.InvalidInputType
        If `table` parameter is not a valid SQLAlchemy Table object or a string.
    Exception
        If any other error occurs.

    Example
    -------
    >>> import sqlalchemize as sz

    >>> engine, table = sz.get_engine_table('sqlite:///data/test.db', 'xy')
    >>> sz.select.select_records_all(table)
    [{'id': 1, 'x': 1, 'y': 2}, {'id': 2, 'x': 2, 'y': 4}]

    >>> sz.delete.delete_all_records(table)
    >>> sz.select.select_records_all(table)
    []
    """
    table, engine = _ex.convert_table_engine(table, engine)
    session = _features.get_session(engine)
    try:
        _session.delete_all_records(table, session)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def delete_records_by_primary_keys(
    table: _t.Union[_sa.Table, str],
    primary_key_values: _t.Sequence[_t.Union[_t.Any, _t.Tuple[_t.Any, ...]]],
    engine: _t.Optional[_sa_engine.Engine] = None,
) -> None:
    """
    Delete records by primary key values (single or composite).

    More efficient than delete_records_by_values() when you only have
    primary key values, not full records.

    Parameters
    ----------
    table : Union[Table, str]
        Table object or name
    primary_key_values : Sequence[Union[Any, Tuple[Any, ...]]]
        For single PK: List[Any]
        For composite PK: List[Tuple[Any, ...]]
    engine : Optional[Engine]
        Engine or connection

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If table has no primary key
        If PK tuple lengths don't match for composite PK

    Examples
    --------
    >>> import fullmetalalchemy as fa
    >>> # Single PK
    >>> fa.delete.delete_records_by_primary_keys(
    ...     'users', [1, 2, 3], engine
    ... )
    >>> # Composite PK
    >>> fa.delete.delete_records_by_primary_keys(
    ...     'memberships',
    ...     [(1, 10), (2, 20)],
    ...     engine
    ... )
    """
    table, engine = _ex.convert_table_engine(table, engine)

    pk_names = _features.primary_key_names(table)
    if not pk_names:
        raise ValueError(f"Table {table.name} has no primary key")

    session = _features.get_session(engine)
    try:
        if len(pk_names) == 1:  # Single PK
            # primary_key_values should be List[Any]
            column = _features.get_column(table, pk_names[0])
            stmt = _sa.delete(table).where(column.in_(primary_key_values))
            session.execute(stmt)
        else:  # Composite PK
            # primary_key_values should be List[Tuple[Any, ...]]
            # Validate tuple lengths
            for pk_tuple in primary_key_values:
                if not isinstance(pk_tuple, tuple):
                    raise ValueError(
                        f"For composite PK, values must be tuples, got {type(pk_tuple)}"
                    )
                if len(pk_tuple) != len(pk_names):
                    raise ValueError(
                        f"PK tuple length {len(pk_tuple)} doesn't match "
                        f"number of PK columns {len(pk_names)}"
                    )

            # Build (col1, col2) IN ((val1, val2), ...) query
            pk_columns = [_features.get_column(table, pk_name) for pk_name in pk_names]
            pk_tuple_expr = _sa.tuple_(*pk_columns)
            stmt = _sa.delete(table).where(pk_tuple_expr.in_(primary_key_values))
            session.execute(stmt)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
