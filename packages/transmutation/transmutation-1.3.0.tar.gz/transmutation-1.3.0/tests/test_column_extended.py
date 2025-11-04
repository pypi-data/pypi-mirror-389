"""Extended tests for column operations."""

import unittest

from setup_test import sqlite_setup
from fullmetalalchemy.features import get_table

import transmutation as tm
from transmutation.exceptions import ValidationError


class TestAlterColumnExtended(unittest.TestCase):
    """Extended tests for alter_column function."""

    def test_alter_column_change_type(self):
        """Test alter_column changing column type."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Add a column with integer type
        tm.add_column("people", "score", int, engine, nullable=True)

        # SQLite has limited type alteration, but should not error
        # For other databases, this would change the type
        result = tm.alter_column("people", "score", engine, type_=float)
        self.assertIsNotNone(result)

    def test_alter_column_with_server_default(self):
        """Test alter_column with server_default parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Alter column to add server default
        result = tm.alter_column("people", "age", engine, server_default="0")
        self.assertIsNotNone(result)

    def test_alter_column_with_default(self):
        """Test alter_column with default parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Alter column to add default
        result = tm.alter_column("people", "age", engine, default=0)
        self.assertIsNotNone(result)

    def test_alter_column_change_nullable(self):
        """Test alter_column changing nullable property."""
        engine, tbl1, tbl2 = sqlite_setup()

        # First make nullable
        result = tm.alter_column("people", "age", engine, nullable=True)
        self.assertTrue(result.columns["age"].nullable)

        # Then make not nullable (requires default for existing rows)
        result = tm.alter_column("people", "age", engine, nullable=False, default=0)
        self.assertFalse(result.columns["age"].nullable)

    def test_alter_column_verify(self):
        """Test alter_column with verify=True."""
        engine, tbl1, tbl2 = sqlite_setup()

        result = tm.alter_column(
            "people", "age", engine, nullable=False, verify=True, default=0
        )
        self.assertIsNotNone(result)

    def test_rename_column_mysql_type_detection(self):
        """Test rename_column with MySQL type detection (if MySQL available)."""
        engine, tbl1, tbl2 = sqlite_setup()

        # SQLite doesn't require type, but test the path exists
        result = tm.rename_column("people", "name", "full_name", engine)
        self.assertIsNotNone(result)

        # Verify rename worked
        table = get_table("people", engine)
        self.assertIn("full_name", table.columns.keys())

    def test_rename_column_with_existing_type(self):
        """Test rename_column with existing_type parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        from sqlalchemy.types import String

        # Ensure column exists first
        table = get_table("people", engine)
        if "full_name" not in table.columns.keys():
            # Rename name to full_name first
            if "name" in table.columns.keys():
                tm.rename_column("people", "name", "full_name", engine)

        # Provide existing type explicitly
        result = tm.rename_column(
            "people", "full_name", "display_name", engine, existing_type=String(20)
        )
        self.assertIsNotNone(result)

    def test_rename_column_verify(self):
        """Test rename_column with verify=True."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Need to ensure 'name' column exists
        # If it was renamed, add it back
        table = get_table("people", engine)
        if "name" not in table.columns.keys():
            tm.add_column("people", "name", str, engine, nullable=True)

        result = tm.rename_column("people", "name", "person_name", engine, verify=True)
        self.assertIsNotNone(result)

        # Verify with new connection
        table = get_table("people", engine)
        self.assertIn("person_name", table.columns.keys())


class TestColumnErrorCases(unittest.TestCase):
    """Tests for column operation error cases."""

    def test_add_column_error_nonexistent_table(self):
        """Test add_column raises error for non-existent table."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.add_column("nonexistent", "col", str, engine)

    def test_drop_column_error_nonexistent_table(self):
        """Test drop_column raises error for non-existent table."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.drop_column("nonexistent", "col", engine)

    def test_drop_column_error_nonexistent_column(self):
        """Test drop_column raises error for non-existent column."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.drop_column("people", "nonexistent", engine)

    def test_rename_column_error_nonexistent_table(self):
        """Test rename_column raises error for non-existent table."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.rename_column("nonexistent", "old", "new", engine)

    def test_rename_column_error_nonexistent_column(self):
        """Test rename_column raises error for non-existent column."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.rename_column("people", "nonexistent", "new", engine)

    def test_alter_column_error_nonexistent_table(self):
        """Test alter_column raises error for non-existent table."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.alter_column("nonexistent", "col", engine)

    def test_alter_column_error_nonexistent_column(self):
        """Test alter_column raises error for non-existent column."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.alter_column("people", "nonexistent", engine)
