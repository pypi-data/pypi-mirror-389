"""Index operations for database schema modifications."""

from typing import List, Optional, Union

from sqlalchemy import Table
from sqlalchemy.engine import Engine, Connection

from transmutation.utils import (
    _get_op,
    _normalize_connection,
    _get_table_with_connection,
    _commit_if_needed,
    validate_table_exists,
    validate_column_exists,
    index_exists,
)
from transmutation.exceptions import IndexError as TransmutationIndexError


def create_index(
    index_name: str,
    table_name: str,
    columns: Union[str, List[str]],
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    unique: bool = False,
    if_not_exists: bool = False,
) -> Table:
    """
    Create an index on one or more columns.

    Args:
        index_name: Name of the index to create
        table_name: Name of the table
        columns: Column name or list of column names
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        unique: Whether to create a unique index (default: False)
        if_not_exists: Skip creation if index already exists (default: False)

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        IndexError: If the create operation fails
        ValidationError: If the table or columns don't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = create_index('idx_email', 'users', 'email', engine, unique=True)
        >>> table = create_index('idx_name', 'users', ['last_name', 'first_name'], engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)

        # Normalize columns to list
        if isinstance(columns, str):
            columns = [columns]

        # Validate all columns exist
        for col in columns:
            validate_column_exists(table_name, col, connection=conn, schema=schema)

        # Check if index already exists
        if if_not_exists and index_exists(
            index_name, table_name, connection=conn, schema=schema
        ):
            return _get_table_with_connection(table_name, conn, schema)

        op = _get_op(connection=conn)
        op.create_index(index_name, table_name, columns, unique=unique, schema=schema)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        _commit_if_needed(conn, should_close)

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise TransmutationIndexError(
            f"Failed to create index '{index_name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()


def drop_index(
    index_name: str,
    table_name: Optional[str] = None,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    if_exists: bool = False,
) -> Optional[Table]:
    """
    Drop an index from a table.

    Args:
        index_name: Name of the index to drop
        table_name: Name of the table (required for some databases)
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        if_exists: Skip if index doesn't exist (default: False)

    Returns:
        Newly reflected SQLAlchemy Table object if table_name provided, else None

    Raises:
        IndexError: If the drop operation fails
        ValidationError: If the table doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> drop_index('idx_email', 'users', engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        if table_name:
            validate_table_exists(table_name, connection=conn, schema=schema)

            # Check if index exists
            if if_exists and not index_exists(
                index_name, table_name, connection=conn, schema=schema
            ):
                return _get_table_with_connection(table_name, conn, schema)

        op = _get_op(connection=conn)
        op.drop_index(index_name, table_name=table_name, schema=schema)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        _commit_if_needed(conn, should_close)

        if table_name:
            return _get_table_with_connection(table_name, conn, schema)
        return None
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise TransmutationIndexError(
            f"Failed to drop index '{index_name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()


def create_unique_index(
    index_name: str,
    table_name: str,
    columns: Union[str, List[str]],
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    if_not_exists: bool = False,
) -> Table:
    """
    Create a unique index on one or more columns.

    This is a convenience function that calls create_index with unique=True.

    Args:
        index_name: Name of the index to create
        table_name: Name of the table
        columns: Column name or list of column names
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        if_not_exists: Skip creation if index already exists (default: False)

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        IndexError: If the create operation fails
        ValidationError: If the table or columns don't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = create_unique_index('idx_unique_email', 'users', 'email', engine)
    """
    return create_index(
        index_name=index_name,
        table_name=table_name,
        columns=columns,
        engine=engine,
        connection=connection,
        schema=schema,
        unique=True,
        if_not_exists=if_not_exists,
    )
