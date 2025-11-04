"""Tests for utility functions."""

import unittest

from setup_test import sqlite_setup
from transmutation import utils


class TestUtilsFunctions(unittest.TestCase):
    """Tests for utility functions."""

    def test_get_dialect_name(self):
        """Test get_dialect_name function."""
        engine, tbl1, tbl2 = sqlite_setup()
        dialect_name = utils.get_dialect_name(engine)
        self.assertEqual(dialect_name, "sqlite")

        # Test with connection
        with engine.connect() as conn:
            dialect_name = utils.get_dialect_name(connection=conn)
            self.assertEqual(dialect_name, "sqlite")

    def test_is_sqlite(self):
        """Test is_sqlite function."""
        engine, tbl1, tbl2 = sqlite_setup()
        self.assertTrue(utils.is_sqlite(engine))

        # Test with connection
        with engine.connect() as conn:
            self.assertTrue(utils.is_sqlite(connection=conn))

    def test_is_postgresql(self):
        """Test is_postgresql function."""
        engine, tbl1, tbl2 = sqlite_setup()
        self.assertFalse(utils.is_postgresql(engine))

        # Test with connection
        with engine.connect() as conn:
            self.assertFalse(utils.is_postgresql(connection=conn))

    def test_is_mysql(self):
        """Test is_mysql function."""
        engine, tbl1, tbl2 = sqlite_setup()
        self.assertFalse(utils.is_mysql(engine))

        # Test with connection
        with engine.connect() as conn:
            self.assertFalse(utils.is_mysql(connection=conn))

    def test_table_exists(self):
        """Test table_exists function."""
        engine, tbl1, tbl2 = sqlite_setup()

        self.assertTrue(utils.table_exists("people", engine))
        self.assertFalse(utils.table_exists("nonexistent", engine))

        # Test with connection
        with engine.connect() as conn:
            self.assertTrue(utils.table_exists("people", connection=conn))
            self.assertFalse(utils.table_exists("nonexistent", connection=conn))

    def test_validate_table_exists_raises(self):
        """Test validate_table_exists raises error for missing table."""
        engine, tbl1, tbl2 = sqlite_setup()

        from transmutation.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            utils.validate_table_exists("nonexistent", engine)

        # Test with connection
        with engine.connect() as conn:
            with self.assertRaises(ValidationError):
                utils.validate_table_exists("nonexistent", connection=conn)

    def test_get_table_names(self):
        """Test get_table_names function."""
        engine, tbl1, tbl2 = sqlite_setup()

        tables = utils.get_table_names(engine)
        self.assertIn("people", tables)
        self.assertIn("places", tables)

        # Test with connection
        with engine.connect() as conn:
            tables = utils.get_table_names(connection=conn)
            self.assertIn("people", tables)
            self.assertIn("places", tables)

    def test_column_exists(self):
        """Test column_exists function."""
        engine, tbl1, tbl2 = sqlite_setup()

        self.assertTrue(utils.column_exists("people", "name", engine))
        self.assertFalse(utils.column_exists("people", "nonexistent", engine))

        # Test with connection
        with engine.connect() as conn:
            self.assertTrue(utils.column_exists("people", "name", connection=conn))
            self.assertFalse(
                utils.column_exists("people", "nonexistent", connection=conn)
            )

    def test_validate_column_exists_raises(self):
        """Test validate_column_exists raises error for missing column."""
        engine, tbl1, tbl2 = sqlite_setup()

        from transmutation.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            utils.validate_column_exists("people", "nonexistent", engine)

        # Test with connection
        with engine.connect() as conn:
            with self.assertRaises(ValidationError):
                utils.validate_column_exists("people", "nonexistent", connection=conn)

    def test_index_exists(self):
        """Test index_exists function."""
        engine, tbl1, tbl2 = sqlite_setup()

        # Create an index first
        import transmutation as tm

        tm.create_index("idx_test", "people", "name", engine)

        self.assertTrue(utils.index_exists("idx_test", "people", engine))
        self.assertFalse(utils.index_exists("idx_nonexistent", "people", engine))

        # Test with connection
        with engine.connect() as conn:
            self.assertTrue(utils.index_exists("idx_test", "people", connection=conn))
            self.assertFalse(
                utils.index_exists("idx_nonexistent", "people", connection=conn)
            )

    def test_get_primary_key_columns(self):
        """Test get_primary_key_columns function."""
        engine, tbl1, tbl2 = sqlite_setup()

        pk_cols = utils.get_primary_key_columns("people", engine)
        self.assertIn("id", pk_cols)

        # Test with connection
        with engine.connect() as conn:
            pk_cols = utils.get_primary_key_columns("people", connection=conn)
            self.assertIn("id", pk_cols)

    def test_get_foreign_keys(self):
        """Test get_foreign_keys function."""
        engine, tbl1, tbl2 = sqlite_setup()

        fks = utils.get_foreign_keys("people", engine)
        # May or may not have foreign keys depending on setup
        self.assertIsInstance(fks, list)

        # Test with connection
        with engine.connect() as conn:
            fks = utils.get_foreign_keys("people", connection=conn)
            self.assertIsInstance(fks, list)

    def test_supports_foreign_keys(self):
        """Test supports_foreign_keys function."""
        engine, tbl1, tbl2 = sqlite_setup()

        # SQLite supports foreign keys but they may not be enabled
        result = utils.supports_foreign_keys(engine)
        self.assertIsInstance(result, bool)

        # Test with connection
        with engine.connect() as conn:
            result = utils.supports_foreign_keys(connection=conn)
            self.assertIsInstance(result, bool)

    def test_transaction_context_with_engine(self):
        """Test transaction_context with engine."""
        engine, tbl1, tbl2 = sqlite_setup()

        with utils.transaction_context(engine) as conn:
            self.assertIsNotNone(conn)
            # Connection should be in a transaction context

    def test_transaction_context_with_connection(self):
        """Test transaction_context with existing connection."""
        engine, tbl1, tbl2 = sqlite_setup()

        with engine.connect() as conn:
            with utils.transaction_context(connection=conn) as ctx_conn:
                self.assertEqual(conn, ctx_conn)

    def test_transaction_context_error_both(self):
        """Test transaction_context raises error when both provided."""
        engine, tbl1, tbl2 = sqlite_setup()

        with engine.connect() as conn:
            with self.assertRaises(ValueError):
                with utils.transaction_context(engine=engine, connection=conn):
                    pass

    def test_transaction_context_error_neither(self):
        """Test transaction_context raises error when neither provided."""
        with self.assertRaises(ValueError):
            with utils.transaction_context():
                pass

    def test_normalize_connection_error_both(self):
        """Test _normalize_connection raises error when both engine and connection provided."""
        engine, tbl1, tbl2 = sqlite_setup()

        with engine.connect() as conn:
            with self.assertRaises(ValueError):
                utils._normalize_connection(engine=engine, connection=conn)

    def test_normalize_connection_error_neither(self):
        """Test _normalize_connection raises error when neither provided."""
        with self.assertRaises(ValueError):
            utils._normalize_connection()
