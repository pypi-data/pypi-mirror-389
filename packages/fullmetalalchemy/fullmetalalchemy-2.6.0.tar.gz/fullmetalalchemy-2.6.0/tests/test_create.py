import pytest
import sqlalchemy as sa

try:
    import pandas as pd

    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False

import fullmetalalchemy as sz
from fullmetalalchemy.create import (
    _column_datatype,
    copy_table,
    create_engine,
    create_table,
    create_table_from_dataframe,
    create_table_from_records,
)
from fullmetalalchemy.features import tables_metadata_equal
from fullmetalalchemy.records import records_equal


@pytest.fixture
def engine():
    """Create a fresh in-memory SQLite engine for each test."""
    return sa.create_engine("sqlite://")


def test_create_table_sqlite(engine):
    """Test creating a table from specifications."""
    create_table(
        table_name="xy",
        column_names=["id", "x", "y"],
        column_types=[int, int, int],
        primary_key=["id"],
        engine=engine,
        if_exists="replace",
    )
    table = sz.features.get_table("xy", engine)
    expected = sa.Table(
        "xy",
        sa.MetaData(),
        sa.Column("id", sa.sql.sqltypes.INTEGER(), primary_key=True, nullable=False),
        sa.Column("x", sa.sql.sqltypes.INTEGER()),
        sa.Column("y", sa.sql.sqltypes.INTEGER()),
        schema=None,
    )
    assert tables_metadata_equal(table, expected)


def test_create_table_from_records_sqlite(engine):
    """Test creating a table from records with automatic type inference."""
    records = [
        {"id": 1, "x": 1, "y": 2},
        {"id": 2, "x": 2, "y": 4},
        {"id": 3, "x": 4, "y": 8},
        {"id": 4, "x": 8, "y": 11},
    ]
    table = create_table_from_records(
        table_name="xy", records=records, primary_key=["id"], engine=engine, if_exists="replace"
    )
    expected = sa.Table(
        "xy",
        sa.MetaData(),
        sa.Column("id", sa.sql.sqltypes.INTEGER(), primary_key=True, nullable=False),
        sa.Column("x", sa.sql.sqltypes.INTEGER()),
        sa.Column("y", sa.sql.sqltypes.INTEGER()),
        schema=None,
    )
    assert tables_metadata_equal(table, expected)
    selected = sz.select.select_records_all(table, engine)
    assert records_equal(selected, records)


def test_create_engine():
    """Test create_engine wrapper function."""
    engine = create_engine("sqlite://")
    assert isinstance(engine, sa.engine.Engine)


def test_copy_table(engine_and_table):
    """Test copying a table to a new table."""
    engine, original_table = engine_and_table

    # Copy the table
    new_table = copy_table("xy_copy", original_table, engine)

    assert new_table.name == "xy_copy"
    # Verify data was copied
    records = sz.select.select_records_all(new_table, engine)
    assert len(records) == 4
    assert records[0] == {"id": 1, "x": 1, "y": 2}


def test_copy_table_with_if_exists_replace(engine_and_table):
    """Test copy_table with if_exists='replace'."""
    engine, original_table = engine_and_table

    # Create table first
    copy_table("xy_copy", original_table, engine, if_exists="replace")
    # Copy again with replace
    new_table = copy_table("xy_copy", original_table, engine, if_exists="replace")

    assert new_table.name == "xy_copy"
    records = sz.select.select_records_all(new_table, engine)
    assert len(records) == 4


def test_column_datatype_float():
    """Test _column_datatype with float values."""
    values = [1.5, 2.7, 3.9]
    result = _column_datatype(values)
    assert result is float


def test_column_datatype_string():
    """Test _column_datatype with string values."""
    values = ["hello", "world", "test"]
    result = _column_datatype(values)
    assert result is str


def test_column_datatype_list():
    """Test _column_datatype with list values."""
    values = [[1, 2], [3, 4]]
    result = _column_datatype(values)
    assert result is list


def test_column_datatype_dict():
    """Test _column_datatype with dict values."""
    values = [{"a": 1}, {"b": 2}]
    result = _column_datatype(values)
    assert result is dict


def test_column_datatype_mixed_fallback():
    """Test _column_datatype falls back to str for mixed types."""
    values = [1, "a", 2.5]
    result = _column_datatype(values)
    assert result is str


def test_create_table_with_autoincrement(engine):
    """Test creating table with autoincrement primary key."""
    table = create_table(
        table_name="test_auto",
        column_names=["id", "value"],
        column_types=[int, str],
        primary_key=["id"],
        engine=engine,
        autoincrement=True,
        if_exists="replace",
    )
    assert table.name == "test_auto"


def test_column_datatype_with_unhashable_types():
    """Test _column_datatype with unhashable types (lists/dicts in values)."""
    # This triggers the TypeError except block when trying to hash
    values = [[1, 2, 3], [4, 5, 6]]  # Lists are unhashable
    result = _column_datatype(values)
    # Should return list type
    assert result is list


def test_column_datatype_all_integers():
    """Test _column_datatype with all integer values."""
    # Integer values match both int and (int, float) tuple
    # Should prefer int (line 216-217)
    values = [1, 2, 3, 4, 5]
    result = _column_datatype(values)
    assert result is int


def test_column_datatype_mixed_int_and_float():
    """Test _column_datatype with mixed int and float values."""
    # Mixed int/float should match only (int, float) tuple
    values = [1, 2.5, 3, 4.7]
    result = _column_datatype(values)
    assert result is float


@pytest.mark.skipif(not _HAS_PANDAS, reason="requires pandas")
def test_create_table_from_dataframe_basic(engine):
    """Test creating table from simple DataFrame."""
    df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"], "score": [95.5, 87.3]})
    table = create_table_from_dataframe("users", df, "id", engine)

    # Verify table was created
    assert sz.features.table_exists("users", engine) is True

    # Check data was inserted
    records = sz.select.select_records_all(table)
    assert len(records) == 2
    assert records[0]["name"] == "Alice"


@pytest.mark.skipif(not _HAS_PANDAS, reason="requires pandas")
def test_create_table_from_dataframe_empty(engine):
    """Test creating table from empty DataFrame."""
    df = pd.DataFrame(columns=["id", "name", "score"])
    table = create_table_from_dataframe("empty_users", df, "id", engine)

    # Verify table was created
    assert sz.features.table_exists("empty_users", engine) is True

    # Check no data was inserted
    records = sz.select.select_records_all(table)
    assert len(records) == 0


@pytest.mark.skipif(not _HAS_PANDAS, reason="requires pandas")
def test_create_table_from_dataframe_dtypes(engine):
    """Test creating table with various dtypes."""
    df = pd.DataFrame(
        {
            "id": pd.Series([1, 2], dtype="int64"),
            "float_col": pd.Series([1.5, 2.5], dtype="float64"),
            "bool_col": pd.Series([True, False], dtype="bool"),
            "str_col": pd.Series(["a", "b"], dtype="object"),
        }
    )
    create_table_from_dataframe("mixed_types", df, "id", engine)

    # Verify table was created
    assert sz.features.table_exists("mixed_types", engine) is True


@pytest.mark.skipif(not _HAS_PANDAS, reason="requires pandas")
def test_create_table_from_dataframe_composite_pk(engine):
    """Test creating table with composite primary key."""
    df = pd.DataFrame(
        {"user_id": [1, 2, 3], "org_id": [10, 10, 20], "role": ["admin", "user", "admin"]}
    )
    create_table_from_dataframe("memberships", df, ["user_id", "org_id"], engine)

    # Verify table was created
    assert sz.features.table_exists("memberships", engine) is True

    # Check composite PK was set correctly
    pk_names = sz.features.get_primary_key_names("memberships", engine)
    assert isinstance(pk_names, list)
    assert pk_names == ["user_id", "org_id"]


@pytest.mark.skipif(not _HAS_PANDAS, reason="requires pandas")
def test_create_table_from_dataframe_datetime(engine):
    """Test creating table with datetime column.

    Note: SQLite doesn't support datetime64[ns] directly, so this test
    verifies that the basic table creation works. For production use,
    consider converting datetime to string for SQLite compatibility.
    """
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "created": ["2023-01-01", "2023-01-02"],  # Use strings for SQLite compatibility
        }
    )
    create_table_from_dataframe("with_dates", df, "id", engine)

    # Verify table was created
    assert sz.features.table_exists("with_dates", engine) is True


@pytest.mark.skipif(not _HAS_PANDAS, reason="requires pandas")
def test_create_table_from_dataframe_missing_pk_column(engine):
    """Test creating table with missing primary key column raises error."""
    df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})

    # Should raise ValueError for missing PK column
    with pytest.raises(ValueError, match="Primary key column 'bad_pk' not in DataFrame"):
        create_table_from_dataframe("users", df, "bad_pk", engine)


@pytest.mark.skipif(not _HAS_PANDAS, reason="requires pandas")
def test_create_table_from_dataframe_replace(engine):
    """Test creating table with if_exists='replace'."""
    df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    table1 = create_table_from_dataframe("replace_test", df1, "id", engine)

    # Insert more data
    sz.insert.insert_records(table1, [{"id": 3, "name": "Charlie"}], engine)
    assert len(sz.select.select_records_all(table1)) == 3

    # Replace with new DataFrame
    df2 = pd.DataFrame({"id": [10, 20], "name": ["David", "Eve"]})
    table2 = create_table_from_dataframe("replace_test", df2, "id", engine, if_exists="replace")

    # Should only have new data
    records = sz.select.select_records_all(table2)
    assert len(records) == 2
    assert records[0]["name"] == "David"


@pytest.mark.skipif(not _HAS_PANDAS, reason="requires pandas")
def test_create_table_from_dataframe_error_if_exists(engine):
    """Test creating table with if_exists='error' raises exception when table exists."""
    df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    create_table_from_dataframe("error_test", df, "id", engine)

    # Should raise exception if table exists
    with pytest.raises((ValueError, sa.exc.OperationalError)):
        create_table_from_dataframe("error_test", df, "id", engine, if_exists="error")


def test_create_table_from_dataframe_without_pandas(engine):
    """Test creating table from DataFrame without pandas raises ImportError."""

    # This test verifies the ImportError is raised when pandas is not available
    # We'll use a mock DataFrame-like object
    class FakeDataFrame:
        def __init__(self):
            self.columns = ["id", "name"]
            self.dtype = lambda col: "int64" if col == "id" else "object"

    # Temporarily set _HAS_PANDAS to False to test error handling
    # This is a bit hacky but tests the actual error path
    import fullmetalalchemy.create as create_module

    original_has_pandas = create_module._HAS_PANDAS
    create_module._HAS_PANDAS = False

    try:
        with pytest.raises(ImportError, match="pandas is required"):
            create_table_from_dataframe("test", FakeDataFrame(), "id", engine)
    finally:
        create_module._HAS_PANDAS = original_has_pandas
