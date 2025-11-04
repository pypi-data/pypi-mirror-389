"""Extended tests for constraint operations."""

import unittest

from setup_test import sqlite_setup

import transmutation as tm
from transmutation.exceptions import ConstraintError, ValidationError


class TestPrimaryKeyOperations(unittest.TestCase):
    """Tests for primary key operations."""

    def test_create_primary_keys(self):
        """Test create_primary_keys with multiple columns."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Create a table without primary key
        from sqlalchemy import Column, Integer, String

        columns = [
            Column("col1", Integer),
            Column("col2", String(50)),
        ]

        tm.create_table("test_pk", columns, engine)

        # Add primary key on single column
        result = tm.create_primary_key("test_pk", "col1", engine)
        self.assertIsNotNone(result)

        # Verify primary key
        pk_cols = tm.utils.get_primary_key_columns("test_pk", engine)
        self.assertIn("col1", pk_cols)

    def test_create_primary_keys_multiple(self):
        """Test create_primary_keys with multiple columns."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Create a table without primary key
        from sqlalchemy import Column, Integer, String

        columns = [
            Column("col1", Integer),
            Column("col2", String(50)),
            Column("col3", Integer),
        ]

        tm.create_table("test_pk2", columns, engine)

        # Add composite primary key
        result = tm.create_primary_keys("test_pk2", ["col1", "col2"], engine)
        self.assertIsNotNone(result)

        # Verify primary key
        pk_cols = tm.utils.get_primary_key_columns("test_pk2", engine)
        self.assertIn("col1", pk_cols)
        self.assertIn("col2", pk_cols)

    def test_create_primary_key_with_connection(self):
        """Test create_primary_key with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Create a table without primary key
        from sqlalchemy import Column, Integer, String

        columns = [Column("col1", Integer), Column("col2", String(50))]

        tm.create_table("test_pk3", columns, engine)

        with engine.begin() as conn:
            result = tm.create_primary_key("test_pk3", "col1", connection=conn)
            self.assertIsNotNone(result)

        # Verify primary key
        pk_cols = tm.utils.get_primary_key_columns("test_pk3", engine)
        self.assertIn("col1", pk_cols)

    def test_replace_primary_key(self):
        """Test replace_primary_key function."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Create a table with a primary key
        from sqlalchemy import Column, Integer
        from fullmetalalchemy.features import get_table

        columns = [
            Column("old_pk", Integer, primary_key=True),
            Column("new_pk_col", Integer),
        ]

        tm.create_table("test_replace_pk", columns, engine)
        table = get_table("test_replace_pk", engine)

        # Replace primary key - function takes Table object
        result = tm.replace_primary_key(table, "new_pk_col", engine)
        self.assertIsNotNone(result)

        # Verify new primary key
        pk_cols = tm.utils.get_primary_key_columns("test_replace_pk", engine)
        self.assertIn("new_pk_col", pk_cols)

    def test_replace_primary_keys(self):
        """Test replace_primary_keys with multiple columns."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Create a table with a primary key
        from sqlalchemy import Column, Integer
        from fullmetalalchemy.features import get_table

        columns = [
            Column("old_pk1", Integer, primary_key=True),
            Column("new_pk1", Integer),
            Column("new_pk2", Integer),
        ]

        tm.create_table("test_replace_pk2", columns, engine)
        table = get_table("test_replace_pk2", engine)

        # Replace with composite primary key - function takes Table object
        result = tm.replace_primary_keys(table, ["new_pk1", "new_pk2"], engine)
        self.assertIsNotNone(result)

        # Verify new primary key
        pk_cols = tm.utils.get_primary_key_columns("test_replace_pk2", engine)
        self.assertIn("new_pk1", pk_cols)
        self.assertIn("new_pk2", pk_cols)


class TestDropConstraint(unittest.TestCase):
    """Tests for drop_constraint operations."""

    def test_drop_constraint_unique(self):
        """Test drop_constraint for unique constraint."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Add a unique constraint first
        tm.add_column("people", "unique_field", str, engine, nullable=True)
        tm.create_unique_constraint("uq_test", "people", "unique_field", engine)

        # Drop the constraint
        result = tm.drop_constraint("uq_test", "people", engine, type_="unique")
        self.assertIsNotNone(result)

    def test_drop_constraint_check(self):
        """Test drop_constraint for check constraint."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Add a check constraint first
        tm.create_check_constraint("ck_age", "people", "age >= 0", engine)

        # Drop the constraint
        result = tm.drop_constraint("ck_age", "people", engine, type_="check")
        self.assertIsNotNone(result)

    def test_drop_constraint_with_connection(self):
        """Test drop_constraint with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Add a check constraint first
        tm.create_check_constraint("ck_test2", "people", "age >= 0", engine)

        with engine.begin() as conn:
            result = tm.drop_constraint(
                "ck_test2", "people", connection=conn, type_="check"
            )
            self.assertIsNotNone(result)

    def test_drop_constraint_error_not_found(self):
        """Test drop_constraint raises error for non-existent constraint."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Should raise error for non-existent constraint
        with self.assertRaises((ConstraintError, ValidationError)):
            tm.drop_constraint("nonexistent", "people", engine, type_="check")


class TestCreateConstraintsExtended(unittest.TestCase):
    """Extended tests for constraint creation."""

    def test_create_unique_constraint_multiple_columns(self):
        """Test create_unique_constraint with multiple columns."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Add columns first
        tm.add_column("people", "email", str, engine, nullable=True)
        tm.add_column("people", "phone", str, engine, nullable=True)

        # Create composite unique constraint
        result = tm.create_unique_constraint(
            "uq_email_phone", "people", ["email", "phone"], engine
        )
        self.assertIsNotNone(result)

    def test_create_foreign_key_with_options(self):
        """Test create_foreign_key with ondelete and onupdate options."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Add place_id column
        tm.add_column("people", "place_id", int, engine, nullable=True)

        # Check if foreign keys are supported
        if not tm.utils.supports_foreign_keys(engine):
            self.skipTest("Foreign keys not supported")

        # Create FK with cascade options
        result = tm.create_foreign_key(
            "fk_place",
            "people",
            "place_id",
            "places",
            "id",
            engine,
            ondelete="CASCADE",
            onupdate="CASCADE",
        )
        self.assertIsNotNone(result)

    def test_create_check_constraint_with_connection(self):
        """Test create_check_constraint with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        with engine.begin() as conn:
            result = tm.create_check_constraint(
                "ck_test3", "people", "age >= 0", connection=conn
            )
            self.assertIsNotNone(result)
