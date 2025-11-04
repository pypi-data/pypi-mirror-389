"""Extended tests for table operations."""

import unittest

from setup_test import sqlite_setup
from fullmetalalchemy.features import get_table

import transmutation as tm
from transmutation.exceptions import TableError, ValidationError


class TestCreateTableAs(unittest.TestCase):
    """Tests for create_table_as function."""

    def test_create_table_as(self):
        """Test create_table_as basic functionality."""
        engine, tbl1, tbl2 = sqlite_setup()

        from sqlalchemy import select

        # Create a SELECT query
        table = get_table("people", engine)
        select_query = select(table).where(table.c.age > 18)

        # Create a new table as a copy with selection
        tm.create_table_as("people_copy", select_query, engine)

        # Verify table was created
        new_table = get_table("people_copy", engine)
        self.assertIsNotNone(new_table)

        # Verify it has columns from people
        self.assertIn("id", new_table.columns.keys())
        self.assertIn("name", new_table.columns.keys())
        self.assertIn("age", new_table.columns.keys())

    def test_create_table_as_with_connection(self):
        """Test create_table_as with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        from sqlalchemy import select

        # Create a SELECT query
        table = get_table("people", engine)
        select_query = select(table).where(table.c.age > 18)

        with engine.begin() as conn:
            result = tm.create_table_as("people_copy2", select_query, connection=conn)
            self.assertIsNotNone(result)

        # Verify table was created
        new_table = get_table("people_copy2", engine)
        self.assertIsNotNone(new_table)

    def test_drop_table_if_exists(self):
        """Test drop_table with if_exists parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Drop existing table
        tm.drop_table("people", engine, if_exists=True)

        # Verify it's gone
        self.assertFalse(tm.utils.table_exists("people", engine))

        # Try to drop non-existent table (should not error with if_exists=True)
        tm.drop_table("nonexistent", engine, if_exists=True)

    def test_drop_table_error_if_not_exists(self):
        """Test drop_table raises error when table doesn't exist and if_exists=False."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises((TableError, ValidationError)):
            tm.drop_table("nonexistent", engine, if_exists=False)

    def test_copy_table_with_connection(self):
        """Test copy_table with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        # copy_table takes a Table object, not table name
        source_table = get_table("people", engine)

        with engine.begin() as conn:
            result = tm.copy_table(source_table, "people_copy3", connection=conn)
            self.assertIsNotNone(result)

        # Verify copy was created
        table = get_table("people_copy3", engine)
        self.assertIsNotNone(table)
        self.assertIn("name", table.columns.keys())

    def test_create_table_with_all_params(self):
        """Test create_table with all optional parameters."""
        engine, tbl1, tbl2 = sqlite_setup()

        from sqlalchemy import Column, Integer, String

        columns = [
            Column("id", Integer, primary_key=True),
            Column("test_name", String(50)),
            Column("test_value", Integer),
        ]

        tm.create_table("test_table", columns, engine)

        # Verify table was created
        table = get_table("test_table", engine)
        self.assertIsNotNone(table)
        self.assertIn("id", table.columns.keys())
        self.assertIn("test_name", table.columns.keys())
        self.assertIn("test_value", table.columns.keys())

    def test_truncate_table_cascade(self):
        """Test truncate_table with cascade parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Insert some data
        import sqlalchemy as sa

        with engine.connect() as conn:
            conn.execute(
                sa.text(
                    'INSERT INTO people (name, age, address_id) VALUES ("Test", 30, 1)'
                )
            )
            conn.commit()

        # Truncate (cascade doesn't do much in SQLite but should not error)
        tm.truncate_table("people", engine, cascade=True)

        # Verify empty
        with engine.connect() as conn:
            result = conn.execute(sa.text("SELECT COUNT(*) FROM people"))
            count = result.scalar()
            self.assertEqual(count, 0)
