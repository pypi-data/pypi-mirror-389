"""Extended tests for index operations."""

import unittest

from setup_test import sqlite_setup
from fullmetalalchemy.features import get_table

import transmutation as tm
from transmutation.exceptions import IndexError, ValidationError


class TestIndexExtended(unittest.TestCase):
    """Extended tests for index operations."""

    def test_drop_index_error_not_found(self):
        """Test drop_index raises error for non-existent index."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises((IndexError, ValidationError)):
            tm.drop_index("nonexistent_index", "people", engine)

    def test_create_index_error_nonexistent_table(self):
        """Test create_index raises error for non-existent table."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.create_index("idx_test", "nonexistent", "col", engine)

    def test_create_index_error_nonexistent_column(self):
        """Test create_index raises error for non-existent column."""
        engine, tbl1, tbl2 = sqlite_setup()

        with self.assertRaises(ValidationError):
            tm.create_index("idx_test", "people", "nonexistent", engine)

    def test_create_unique_index_with_connection(self):
        """Test create_unique_index with connection parameter."""
        engine, tbl1, tbl2 = sqlite_setup()

        table = get_table("people", engine)

        with engine.begin() as conn:
            result = tm.create_unique_index(
                "uq_idx_test", table.name, "name", connection=conn
            )
            self.assertIsNotNone(result)

        # Verify index was created
        import sqlalchemy as sa

        inspector = sa.inspect(engine)
        indexes = inspector.get_indexes(table.name)
        index_names = [idx["name"] for idx in indexes]
        self.assertIn("uq_idx_test", index_names)

    def test_create_index_unique(self):
        """Test create_index with unique=True."""
        engine, tbl1, tbl2 = sqlite_setup()

        table = get_table("people", engine)

        result = tm.create_index(
            "idx_unique_test", table.name, "age", engine, unique=True
        )
        self.assertIsNotNone(result)

        # Verify unique index was created
        import sqlalchemy as sa

        inspector = sa.inspect(engine)
        indexes = inspector.get_indexes(table.name)
        unique_indexes = [idx for idx in indexes if idx["name"] == "idx_unique_test"]
        self.assertTrue(len(unique_indexes) > 0)
