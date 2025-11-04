"""Tests for connection-based operations and new features."""

import unittest
from sqlalchemy import text

from setup_test import sqlite_setup
from fullmetalalchemy.features import get_table
import transmutation as tm


class TestConnectionOperations(unittest.TestCase):
    """Tests for connection-based operations."""

    def test_add_column_with_connection(self):
        """Test add_column with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        with engine.connect() as conn:
            result = tm.add_column(
                table.name, "middle_name", str, connection=conn, nullable=True
            )
            self.assertIn("middle_name", result.columns.keys())

        # Verify with new connection
        table = get_table("people", engine)
        self.assertIn("middle_name", table.columns.keys())

    def test_add_column_with_verify(self):
        """Test add_column with verify=True."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        result = tm.add_column(
            table.name, "nickname", str, engine, verify=True, nullable=True
        )
        self.assertIn("nickname", result.columns.keys())

    def test_add_column_default_varchar_length(self):
        """Test add_column with default_varchar_length parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        # Test with explicit varchar length
        result = tm.add_column(
            table.name, "description", str, engine, default_varchar_length=500
        )
        self.assertIn("description", result.columns.keys())

    def test_rename_column_with_connection(self):
        """Test rename_column with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        with engine.begin() as conn:  # Use begin() to auto-commit
            tm.rename_column(table.name, "name", "full_name", connection=conn)
            # The result might reflect the table before transaction commits
            # So check the actual database after transaction

        # Verify with new connection (after transaction commits)
        table = get_table("people", engine)
        self.assertIn("full_name", table.columns.keys())
        self.assertNotIn("name", table.columns.keys())

    def test_rename_column_with_verify(self):
        """Test rename_column with verify=True."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        result = tm.rename_column(
            table.name, "name", "display_name", engine, verify=True
        )
        self.assertIn("display_name", result.columns.keys())

    def test_drop_column_with_connection(self):
        """Test drop_column with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        # Add a column first
        tm.add_column(table.name, "temp_col", str, engine, nullable=True)
        table = get_table("people", engine)  # Refresh table

        with engine.begin() as conn:  # Use begin() to auto-commit
            tm.drop_column(table.name, "temp_col", connection=conn)
            # Result might reflect before commit, check after transaction

        # Verify with new connection (after transaction commits)
        table = get_table("people", engine)
        self.assertNotIn("temp_col", table.columns.keys())

    def test_drop_column_with_verify(self):
        """Test drop_column with verify=True."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        # Add a column first
        tm.add_column(table.name, "temp_col2", str, engine, nullable=True)

        result = tm.drop_column(table.name, "temp_col2", engine, verify=True)
        self.assertNotIn("temp_col2", result.columns.keys())

    def test_alter_column_with_connection(self):
        """Test alter_column with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        with engine.begin() as conn:  # Use begin() to auto-commit
            tm.alter_column(
                table.name,
                "age",
                connection=conn,
                nullable=False,
            )
            # Result might reflect before commit

        # Verify with new connection (after transaction commits)
        table = get_table("people", engine)
        self.assertFalse(table.columns["age"].nullable)

    def test_rename_table_with_connection(self):
        """Test rename_table with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        with engine.connect() as conn:
            result = tm.rename_table(table.name, "staff", connection=conn)
            self.assertEqual(result.name, "staff")

        # Verify with new connection
        import sqlalchemy as sa

        inspector = sa.inspect(engine)
        tables = inspector.get_table_names()
        self.assertIn("staff", tables)

    def test_create_index_with_connection(self):
        """Test create_index with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        with engine.connect() as conn:
            result = tm.create_index("idx_test", table.name, "age", connection=conn)
            self.assertIsNotNone(result)

    def test_create_index_if_not_exists(self):
        """Test create_index with if_not_exists parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        # Create index first time
        tm.create_index("idx_ifexists", table.name, "age", engine)

        # Try to create again with if_not_exists=True (should not error)
        result = tm.create_index(
            "idx_ifexists", table.name, "age", engine, if_not_exists=True
        )
        self.assertIsNotNone(result)

    def test_drop_index_with_connection(self):
        """Test drop_index with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        # Create index first
        tm.create_index("idx_droptest", table.name, "age", engine)

        with engine.connect() as conn:
            result = tm.drop_index(
                "idx_droptest", table_name=table.name, connection=conn
            )
            self.assertIsNotNone(result)

    def test_create_foreign_key_with_connection(self):
        """Test create_foreign_key with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        # tbl2 is "places" table from setup, not "addresses"
        # Remove existing FK if any
        try:
            from transmutation.constraint import drop_constraint

            drop_constraint("fk_place", "people", engine, type_="foreignkey")
        except Exception:
            pass

        # First, add a place_id column to people
        tm.add_column("people", "place_id", int, engine, nullable=True)

        # SQLite requires foreign keys to be enabled
        # Check if foreign keys are supported
        from transmutation.utils import supports_foreign_keys

        if not supports_foreign_keys(engine):
            # Skip test if foreign keys not supported
            self.skipTest("Foreign keys not supported or not enabled on this database")

        with engine.begin() as conn:  # Use begin() to auto-commit
            result = tm.create_foreign_key(
                "fk_test",
                "people",
                "place_id",
                "places",
                "id",
                connection=conn,
            )
            # Result might reflect before commit, but operation should succeed
            self.assertIsNotNone(result)

        # Verify FK was created (after transaction commits)
        # FK constraint should exist now

    def test_create_unique_constraint_with_connection(self):
        """Test create_unique_constraint with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        # Add a column first
        tm.add_column(table.name, "unique_field", str, engine, nullable=True)

        with engine.connect() as conn:
            result = tm.create_unique_constraint(
                "uq_test", table.name, "unique_field", connection=conn
            )
            self.assertIsNotNone(result)

    def test_create_check_constraint_with_connection(self):
        """Test create_check_constraint with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        with engine.connect() as conn:
            result = tm.create_check_constraint(
                "ck_test", table.name, "age >= 0", connection=conn
            )
            self.assertIsNotNone(result)

    def test_truncate_table_with_connection(self):
        """Test truncate_table with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        # Insert some data
        with engine.connect() as conn:
            conn.execute(
                text(
                    'INSERT INTO people (name, age, address_id) VALUES ("Test", 30, 1)'
                )
            )
            conn.commit()

        # Truncate with connection using begin() for auto-commit
        with engine.begin() as conn:
            tm.truncate_table(table.name, connection=conn)

        # Verify empty
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM people"))
            count = result.scalar()
            self.assertEqual(count, 0)

    def test_transaction_context(self):
        """Test transaction_context utility."""
        from transmutation.utils import transaction_context

        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        # Test with engine
        with transaction_context(engine) as conn:
            tm.add_column(table.name, "tx_col", str, connection=conn)

        # Verify column exists after transaction
        table = get_table("people", engine)
        self.assertIn("tx_col", table.columns.keys())

    def test_error_both_engine_and_connection(self):
        """Test that providing both engine and connection raises error."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        with engine.connect() as conn:
            with self.assertRaises(ValueError):
                tm.add_column(table.name, "test", str, engine=engine, connection=conn)

    def test_error_neither_engine_nor_connection(self):
        """Test that providing neither engine nor connection raises error."""
        engine, tbl1, tbl2 = sqlite_setup()
        table = get_table("people", engine)

        with self.assertRaises(ValueError):
            tm.add_column(table.name, "test", str, engine=None, connection=None)
