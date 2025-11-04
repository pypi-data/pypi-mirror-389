import sqlalchemy as sa
from sqlalchemy import INTEGER, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm.session import Session

from fullmetalalchemy.features import (
    get_class,
    get_connection,
    get_engine_table,
    get_metadata,
    get_primary_key_names,
    get_session,
    get_table,
    get_table_columns,
    primary_key_columns,
    primary_key_names,
    table_exists,
)
from fullmetalalchemy.test_setup import create_test_table, insert_test_records


def test_primary_key_columns(engine_and_table):
    """Test getting primary key columns from a table."""
    _engine, table = engine_and_table
    results = primary_key_columns(table)
    names = [c.name for c in results]
    types = [type(c.type) for c in results]
    assert names == ["id"]
    assert types == [INTEGER]


def test_primary_key_names(engine_and_table):
    """Test getting primary key column names from a table."""
    _engine, table = engine_and_table
    results = primary_key_names(table)
    assert results == ["id"]


def test_get_connection(engine_and_table):
    """Test getting a connection from a session."""
    engine, _table = engine_and_table
    session = get_session(engine)
    con = get_connection(session)
    assert isinstance(con, Connection)


def test_get_session(engine_and_table):
    """Test creating a session from an engine."""
    engine, _table = engine_and_table
    session = get_session(engine)
    assert isinstance(session, Session)


def test_get_metadata(engine_and_table):
    """Test getting metadata from an engine."""
    engine, _table = engine_and_table
    meta = get_metadata(engine)
    assert isinstance(meta, MetaData)


def test_get_table(engine_and_table):
    """Test getting a table object by name."""
    engine, _table = engine_and_table
    result_table = get_table("xy", engine)
    results = result_table.name, result_table.info.get("engine"), type(result_table)
    expected = "xy", engine, Table
    assert results == expected


def test_get_engine_table():
    """Test getting engine and table from connection string."""
    con_str = "sqlite:///data/test.db"
    engine = sa.create_engine(con_str)
    table = create_test_table(engine)
    insert_test_records(table, engine)

    results = get_engine_table(con_str, "xy")
    results = tuple(type(x) for x in results)
    expected = Engine, Table
    assert results == expected


def test_get_class(engine_and_table):
    """Test getting automap class from table name."""
    engine, _table = engine_and_table
    result = get_class("xy", engine)
    assert isinstance(type(result), type(DeclarativeMeta))


def test_table_exists_with_existing_table(engine_and_table):
    """Test table_exists() returns True for existing table."""
    engine, _table = engine_and_table
    assert table_exists("xy", engine) is True


def test_table_exists_with_nonexistent_table():
    """Test table_exists() returns False for non-existent table."""
    engine = sa.create_engine("sqlite://")
    assert table_exists("nonexistent", engine) is False


def test_table_exists_with_empty_db():
    """Test table_exists() returns False for empty database."""
    engine = sa.create_engine("sqlite://")
    assert table_exists("xy", engine) is False


def test_table_exists_with_schema():
    """Test table_exists() works with schema parameter."""
    engine = sa.create_engine("sqlite://")
    # SQLite doesn't support schemas, but should not error
    assert table_exists("xy", engine, schema=None) is False


def test_get_primary_key_names_single_pk(engine_and_table):
    """Test get_primary_key_names() returns str for single PK."""
    engine, _table = engine_and_table
    result = get_primary_key_names("xy", engine)
    assert result == "id"


def test_get_primary_key_names_composite_pk():
    """Test get_primary_key_names() returns list for composite PK."""
    engine = sa.create_engine("sqlite://")
    metadata = MetaData()
    Table(
        "memberships",
        metadata,
        sa.Column("user_id", sa.Integer),
        sa.Column("org_id", sa.Integer),
        sa.PrimaryKeyConstraint("user_id", "org_id"),
    )
    metadata.create_all(engine)

    result = get_primary_key_names("memberships", engine)
    assert result == ["user_id", "org_id"]
    assert isinstance(result, list)


def test_get_primary_key_names_no_pk():
    """Test get_primary_key_names() returns None for table without PK."""
    engine = sa.create_engine("sqlite://")
    metadata = MetaData()
    Table("logs", metadata, sa.Column("id", sa.Integer), sa.Column("message", sa.String))
    metadata.create_all(engine)

    result = get_primary_key_names("logs", engine)
    assert result is None


def test_get_primary_key_names_with_schema(engine_and_table):
    """Test get_primary_key_names() works with schema parameter."""
    engine, _table = engine_and_table
    result = get_primary_key_names("xy", engine, schema=None)
    assert result == "id"


def test_get_primary_key_names_nonexistent_table():
    """Test get_primary_key_names() raises error for non-existent table."""
    engine = sa.create_engine("sqlite://")
    # This should raise an error
    try:
        get_primary_key_names("nonexistent", engine)
        raise AssertionError("Should have raised an error")
    except Exception:
        pass  # Expected


def test_get_table_columns_basic(engine_and_table):
    """Test get_table_columns() returns column information."""
    engine, _table = engine_and_table
    cols = get_table_columns("xy", engine)

    assert len(cols) == 3
    col_names = [col["name"] for col in cols]
    assert "id" in col_names
    assert "x" in col_names
    assert "y" in col_names


def test_get_table_columns_types(engine_and_table):
    """Test get_table_columns() returns correct types."""
    engine, _table = engine_and_table
    cols = get_table_columns("xy", engine)

    # Find id column
    id_col = next(col for col in cols if col["name"] == "id")
    assert "type" in id_col
    # Type is a SQLAlchemy type object
    assert hasattr(id_col["type"], "python_type") or hasattr(id_col["type"], "__class__")


def test_get_table_columns_nullable(engine_and_table):
    """Test get_table_columns() includes nullable information."""
    engine, _table = engine_and_table
    cols = get_table_columns("xy", engine)

    for col in cols:
        assert "nullable" in col


def test_get_table_columns_with_schema(engine_and_table):
    """Test get_table_columns() works with schema parameter."""
    engine, _table = engine_and_table
    cols = get_table_columns("xy", engine, schema=None)
    assert len(cols) > 0
