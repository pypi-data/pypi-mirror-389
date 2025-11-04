"""Table operations for database schema modifications."""

from typing import Optional, List, Any

from sqlalchemy import Table, Column, MetaData, text
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.sql import Select

from fullmetalalchemy.insert import insert_from_table
from fullmetalalchemy.drop import drop_table as fullmetalalchemy_drop_table

from transmutation.utils import (
    _get_op,
    _normalize_connection,
    _get_table_with_connection,
    _commit_if_needed,
    validate_table_exists,
    table_exists,
)
from transmutation.exceptions import TableError


def rename_table(
    old_table_name: str,
    new_table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> Table:
    """
    Rename a table.

    Args:
        old_table_name: Current name of the table
        new_table_name: New name for the table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        TableError: If the rename operation fails
        ValidationError: If the table doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = rename_table('old_users', 'users', engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(old_table_name, connection=conn, schema=schema)

        op = _get_op(connection=conn)
        op.rename_table(old_table_name, new_table_name, schema=schema)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        _commit_if_needed(conn, should_close)

        return _get_table_with_connection(new_table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise TableError(f"Failed to rename table '{old_table_name}': {str(e)}") from e
    finally:
        if should_close:
            conn.close()


def create_table(
    table_name: str,
    columns: List[Column[Any]],
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    if_not_exists: bool = False,
) -> Table:
    """
    Create a new table with the specified columns.

    Args:
        table_name: Name for the new table
        columns: List of SQLAlchemy Column objects
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        if_not_exists: Skip creation if table already exists (default: False)

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        TableError: If the create operation fails
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine, Column, Integer, String
        >>> engine = create_engine('sqlite:///test.db')
        >>> columns = [
        ...     Column('id', Integer, primary_key=True),
        ...     Column('name', String(50), nullable=False)
        ... ]
        >>> table = create_table('users', columns, engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        if if_not_exists and table_exists(table_name, connection=conn, schema=schema):
            return _get_table_with_connection(table_name, conn, schema)

        op = _get_op(connection=conn)
        metadata = MetaData()

        op.create_table(table_name, *columns, metadata, schema=schema)  # type: ignore

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        raise TableError(f"Failed to create table '{table_name}': {str(e)}") from e
    finally:
        if should_close:
            conn.close()


def drop_table(
    table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    cascade: bool = False,
    if_exists: bool = False,
) -> None:
    """
    Drop a table from the database.

    Args:
        table_name: Name of the table to drop
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        cascade: Drop dependent objects (default: False)
        if_exists: Skip if table doesn't exist (default: False)

    Raises:
        TableError: If the drop operation fails
        ValidationError: If the table doesn't exist and if_exists is False
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> drop_table('old_table', engine, if_exists=True)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        if if_exists and not table_exists(table_name, connection=conn, schema=schema):
            return

        validate_table_exists(table_name, connection=conn, schema=schema)

        op = _get_op(connection=conn)
        op.drop_table(table_name, schema=schema)  # type: ignore

    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise TableError(f"Failed to drop table '{table_name}': {str(e)}") from e
    finally:
        if should_close:
            conn.close()


def copy_table(
    table: Table,
    new_table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    if_exists: str = "replace",
    schema: Optional[str] = None,
    copy_data: bool = True,
) -> Table:
    """
    Create a copy of a table with a new name.

    Args:
        table: SQLAlchemy Table object to copy
        new_table_name: Name for the new table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        if_exists: Action if table exists ('replace', 'fail', 'skip')
        schema: Optional schema name
        copy_data: Whether to copy data from source table (default: True)

    Returns:
        The new SQLAlchemy Table object

    Raises:
        TableError: If the copy operation fails
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> from fullmetalalchemy.features import get_table
        >>> engine = create_engine('sqlite:///test.db')
        >>> source_table = get_table('users', engine)
        >>> new_table = copy_table(source_table, 'users_backup', engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        # Handle if_exists logic
        if table_exists(new_table_name, connection=conn, schema=schema):
            if if_exists == "fail":
                raise TableError(f"Table '{new_table_name}' already exists")
            elif if_exists == "skip":
                return _get_table_with_connection(new_table_name, conn, schema)
            elif if_exists == "replace":
                # Use connection's engine for fullmetalalchemy
                fullmetalalchemy_drop_table(new_table_name, conn.engine, schema=schema)

        op = _get_op(connection=conn)
        op.create_table(new_table_name, *table.c, table.metadata, schema=schema)  # type: ignore

        new_table = _get_table_with_connection(new_table_name, conn, schema)

        # Copy data if requested (insert_from_table may need engine)
        if copy_data:
            insert_from_table(table, new_table, conn.engine)

        return new_table
    except Exception as e:
        if hasattr(e, "__class__") and "TableError" in e.__class__.__name__:
            raise
        raise TableError(
            f"Failed to copy table '{table.name}' to '{new_table_name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()


def truncate_table(
    table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    cascade: bool = False,
) -> None:
    """
    Truncate all data from a table.

    Note: TRUNCATE is not supported on all databases. Falls back to DELETE if needed.

    Args:
        table_name: Name of the table to truncate
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        cascade: Cascade truncation to dependent tables (default: False)

    Raises:
        TableError: If the truncate operation fails
        ValidationError: If the table doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> truncate_table('temp_data', engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)

        # Build fully qualified table name
        full_table_name = f"{schema}.{table_name}" if schema else table_name

        # Use provided connection or start transaction
        # If connection was provided, it might already be in a transaction
        # If we created it, we need to manage the transaction
        was_in_transaction = conn.in_transaction()

        try:
            cascade_clause = " CASCADE" if cascade else ""
            conn.execute(text(f"TRUNCATE TABLE {full_table_name}{cascade_clause}"))
        except Exception:
            # Fall back to DELETE for databases that don't support TRUNCATE
            conn.execute(text(f"DELETE FROM {full_table_name}"))

        # Commit if transmutation created the connection and it needs a commit
        # Note: Some operations (like DELETE) may start a transaction
        _commit_if_needed(conn, should_close, was_in_transaction)

    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise TableError(f"Failed to truncate table '{table_name}': {str(e)}") from e
    finally:
        if should_close:
            conn.close()


def create_table_as(
    table_name: str,
    select_query: Select[Any],
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    if_not_exists: bool = False,
) -> Table:
    """
    Create a table from a SELECT query (CREATE TABLE AS SELECT).

    Note: This uses database-specific SQL and may have limitations.

    Args:
        table_name: Name for the new table
        select_query: SQLAlchemy Select object
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        if_not_exists: Skip creation if table already exists (default: False)

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        TableError: If the create operation fails
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine, select
        >>> from fullmetalalchemy.features import get_table
        >>> engine = create_engine('sqlite:///test.db')
        >>> users = get_table('users', engine)
        >>> query = select(users).where(users.c.active == True)
        >>> new_table = create_table_as('active_users', query, engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        if if_not_exists and table_exists(table_name, connection=conn, schema=schema):
            return _get_table_with_connection(table_name, conn, schema)

        # Build fully qualified table name
        full_table_name = f"{schema}.{table_name}" if schema else table_name

        # Compile the select query (use connection's dialect)
        compiled = select_query.compile(conn, compile_kwargs={"literal_binds": True})

        # Execute CREATE TABLE AS SELECT
        # Use provided connection or manage transaction
        if should_close:
            trans = conn.begin()
            try:
                create_sql = f"CREATE TABLE {full_table_name} AS {compiled}"
                conn.execute(text(create_sql))
                trans.commit()
            except Exception:
                trans.rollback()
                raise
        else:
            create_sql = f"CREATE TABLE {full_table_name} AS {compiled}"
            conn.execute(text(create_sql))

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        raise TableError(
            f"Failed to create table '{table_name}' from SELECT: {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()
