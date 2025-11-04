"""Tests for connection-based operations."""

import pytest
import sqlalchemy as sa
from sqlalchemy import MetaData, Table

import fullmetalalchemy as fa
from fullmetalalchemy.connection import (
    delete_records_connection,
    insert_records_connection,
    update_records_connection,
)


@pytest.fixture
def engine_and_table():
    """Create a fresh in-memory SQLite engine and table for each test."""
    engine = sa.create_engine("sqlite://")
    metadata = MetaData()
    table = Table(
        "test_table",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
        sa.Column("value", sa.Integer),
    )
    metadata.create_all(engine)

    # Insert test data
    with engine.begin() as conn:
        conn.execute(
            table.insert(),
            [
                {"id": 1, "name": "Alice", "value": 10},
                {"id": 2, "name": "Bob", "value": 20},
                {"id": 3, "name": "Charlie", "value": 30},
            ],
        )

    return engine, table


def test_insert_records_connection_basic(engine_and_table):
    """Test basic insert using connection."""
    engine, _table = engine_and_table

    with engine.begin() as conn:
        insert_records_connection("test_table", [{"id": 4, "name": "David", "value": 40}], conn)

    # Verify insert
    records = fa.select.select_records_all("test_table", engine)
    assert len(records) == 4
    assert records[-1]["name"] == "David"


def test_insert_records_connection_with_table_object(engine_and_table):
    """Test insert using connection with Table object."""
    engine, table = engine_and_table

    with engine.begin() as conn:
        insert_records_connection(table, [{"id": 4, "name": "David", "value": 40}], conn)

    records = fa.select.select_records_all(table, engine)
    assert len(records) == 4


def test_update_records_connection_by_pk(engine_and_table):
    """Test update using connection with primary key matching."""
    engine, _table = engine_and_table

    with engine.begin() as conn:
        update_records_connection("test_table", [{"id": 1, "name": "Alice Updated"}], conn)

    # Verify update
    records = fa.select.select_records_all("test_table", engine)
    alice = next(r for r in records if r["id"] == 1)
    assert alice["name"] == "Alice Updated"
    assert alice["value"] == 10  # Should be unchanged


def test_update_records_connection_multiple(engine_and_table):
    """Test update multiple records using connection."""
    engine, _table = engine_and_table

    with engine.begin() as conn:
        update_records_connection(
            "test_table",
            [
                {"id": 1, "value": 15},
                {"id": 2, "value": 25},
            ],
            conn,
        )

    records = fa.select.select_records_all("test_table", engine)
    assert records[0]["value"] == 15
    assert records[1]["value"] == 25


def test_update_records_connection_rollback(engine_and_table):
    """Test that rollback works with connection operations."""
    engine, _table = engine_and_table

    # Insert within transaction then rollback
    conn = engine.connect()
    trans = conn.begin()
    try:
        insert_records_connection(
            "test_table", [{"id": 99, "name": "Should not exist", "value": 99}], conn
        )
        trans.rollback()
    finally:
        conn.close()

    # Verify rollback
    records = fa.select.select_records_all("test_table", engine)
    assert len(records) == 3
    assert not any(r["id"] == 99 for r in records)


def test_delete_records_connection_by_column(engine_and_table):
    """Test delete using connection by column values."""
    engine, _table = engine_and_table

    with engine.begin() as conn:
        delete_records_connection("test_table", conn, column_name="value", values=[10, 20])

    records = fa.select.select_records_all("test_table", engine)
    assert len(records) == 1
    assert records[0]["name"] == "Charlie"


def test_delete_records_connection_by_primary_key_single(engine_and_table):
    """Test delete using connection by single primary key."""
    engine, _table = engine_and_table

    with engine.begin() as conn:
        delete_records_connection("test_table", conn, primary_key_values=[1, 3])

    records = fa.select.select_records_all("test_table", engine)
    assert len(records) == 1
    assert records[0]["name"] == "Bob"


def test_delete_records_connection_by_composite_primary_key():
    """Test delete using connection by composite primary key."""
    engine = sa.create_engine("sqlite://")
    metadata = MetaData()
    table = Table(
        "memberships",
        metadata,
        sa.Column("user_id", sa.Integer),
        sa.Column("org_id", sa.Integer),
        sa.Column("role", sa.String),
        sa.PrimaryKeyConstraint("user_id", "org_id"),
    )
    metadata.create_all(engine)

    # Insert data
    with engine.begin() as conn:
        conn.execute(
            table.insert(),
            [
                {"user_id": 1, "org_id": 10, "role": "admin"},
                {"user_id": 2, "org_id": 10, "role": "user"},
                {"user_id": 1, "org_id": 20, "role": "admin"},
            ],
        )

    # Delete by composite PK
    with engine.begin() as conn:
        delete_records_connection("memberships", conn, primary_key_values=[(1, 10), (1, 20)])

    records = fa.select.select_records_all("memberships", engine)
    assert len(records) == 1
    assert records[0]["user_id"] == 2


def test_delete_records_connection_by_records(engine_and_table):
    """Test delete using connection by record matching."""
    engine, _table = engine_and_table

    with engine.begin() as conn:
        delete_records_connection(
            "test_table",
            conn,
            records=[
                {"id": 1, "name": "Alice", "value": 10},
                {"id": 2, "name": "Bob", "value": 20},
            ],
        )

    records = fa.select.select_records_all("test_table", engine)
    assert len(records) == 1


def test_delete_records_connection_no_pk():
    """Test delete with table that has no primary key raises error."""
    engine = sa.create_engine("sqlite://")
    metadata = MetaData()
    Table("logs", metadata, sa.Column("id", sa.Integer), sa.Column("message", sa.String))
    metadata.create_all(engine)

    with pytest.raises(ValueError, match="Table has no primary key"):
        with engine.begin() as conn:
            delete_records_connection("logs", conn, primary_key_values=[1])


def test_delete_records_connection_no_criteria(engine_and_table):
    """Test delete with no deletion criteria raises error."""
    engine, _table = engine_and_table

    with pytest.raises(ValueError, match="Must provide deletion criteria"):
        with engine.begin() as conn:
            delete_records_connection("test_table", conn)


def test_update_records_connection_no_pk():
    """Test update without primary key and no match_column_names raises error."""
    engine = sa.create_engine("sqlite://")
    metadata = MetaData()
    Table("logs", metadata, sa.Column("id", sa.Integer), sa.Column("message", sa.String))
    metadata.create_all(engine)

    with pytest.raises(ValueError, match="Table has no primary key"):
        with engine.begin() as conn:
            update_records_connection("logs", [{"id": 1, "message": "updated"}], conn)


@pytest.fixture
def composite_table():
    """Create table with composite primary key."""
    engine = sa.create_engine("sqlite://")
    metadata = MetaData()
    table = Table(
        "composite_test",
        metadata,
        sa.Column("pk1", sa.Integer),
        sa.Column("pk2", sa.Integer),
        sa.Column("data", sa.String),
        sa.PrimaryKeyConstraint("pk1", "pk2"),
    )
    metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(
            table.insert(),
            [
                {"pk1": 1, "pk2": 10, "data": "A"},
                {"pk1": 1, "pk2": 20, "data": "B"},
                {"pk1": 2, "pk2": 10, "data": "C"},
            ],
        )

    return engine, table


def test_update_with_match_columns(composite_table):
    """Test update with explicit match_column_names for composite PK."""
    engine, _table = composite_table

    with engine.begin() as conn:
        update_records_connection(
            "composite_test",
            [{"pk1": 1, "pk2": 10, "data": "Updated"}],
            conn,
            match_column_names=["pk1", "pk2"],
        )

    records = fa.select.select_records_all("composite_test", engine)
    updated = next(r for r in records if r["pk1"] == 1 and r["pk2"] == 10)
    assert updated["data"] == "Updated"
