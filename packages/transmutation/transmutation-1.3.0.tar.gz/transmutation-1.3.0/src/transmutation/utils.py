"""Utility functions for transmutation operations."""

from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from sqlalchemy.engine import Engine, Connection
from sqlalchemy import Table, inspect, text as sql_text
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations

from transmutation.exceptions import ValidationError


def _normalize_connection(
    engine: Optional[Engine] = None, connection: Optional[Connection] = None
) -> Tuple[Connection, bool]:
    """
    Normalize engine/connection input to a connection.

    Args:
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)

    Returns:
        (connection, should_close): Tuple where should_close indicates
        if the connection was created internally and should be closed.

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    if engine is None and connection is None:
        raise ValueError("Either engine or connection must be provided")
    if engine is not None and connection is not None:
        raise ValueError("Cannot provide both engine and connection")

    if connection is not None:
        return connection, False
    else:
        # Create connection from engine - caller must close it
        # mypy: engine is guaranteed to be not None here due to validation above
        assert engine is not None  # Type narrowing for mypy
        return engine.connect(), True


def _get_op(
    engine: Optional[Engine] = None, connection: Optional[Connection] = None
) -> Operations:
    """
    Create an Alembic Operations object for the given engine or connection.

    Args:
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)

    Returns:
        Alembic Operations instance

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    conn, should_close = _normalize_connection(engine, connection)
    ctx = MigrationContext.configure(conn)
    op = Operations(ctx)
    # Note: We don't close connection here because Operations needs it
    # Caller is responsible for closing if should_close is True
    return op


def get_dialect_name(
    engine: Optional[Engine] = None, connection: Optional[Connection] = None
) -> str:
    """
    Get the database dialect name from the engine or connection.

    Args:
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)

    Returns:
        Dialect name (e.g., 'sqlite', 'postgresql', 'mysql')

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    if connection is not None:
        return connection.dialect.name
    elif engine is not None:
        return engine.dialect.name
    else:
        raise ValueError("Either engine or connection must be provided")


def is_sqlite(
    engine: Optional[Engine] = None, connection: Optional[Connection] = None
) -> bool:
    """Check if the engine or connection is for SQLite."""
    return get_dialect_name(engine=engine, connection=connection) == "sqlite"


def is_postgresql(
    engine: Optional[Engine] = None, connection: Optional[Connection] = None
) -> bool:
    """Check if the engine or connection is for PostgreSQL."""
    return get_dialect_name(engine=engine, connection=connection) == "postgresql"


def is_mysql(
    engine: Optional[Engine] = None, connection: Optional[Connection] = None
) -> bool:
    """Check if the engine or connection is for MySQL."""
    return get_dialect_name(engine=engine, connection=connection) in (
        "mysql",
        "mariadb",
    )


def table_exists(
    table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> bool:
    """
    Check if a table exists in the database.

    Args:
        table_name: Name of the table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        True if table exists, False otherwise

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        inspector = inspect(conn)
        return inspector.has_table(table_name, schema=schema)
    finally:
        if should_close:
            conn.close()


def validate_table_exists(
    table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> None:
    """
    Validate that a table exists, raise ValidationError if not.

    Args:
        table_name: Name of the table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Raises:
        ValidationError: If table does not exist
        ValueError: If both engine and connection are provided, or neither is provided
    """
    if not table_exists(
        table_name, engine=engine, connection=connection, schema=schema
    ):
        schema_msg = f" in schema '{schema}'" if schema else ""
        raise ValidationError(f"Table '{table_name}' does not exist{schema_msg}")


def get_table_names(
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> List[str]:
    """
    Get list of all table names in the database.

    Args:
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        List of table names

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        inspector = inspect(conn)
        return inspector.get_table_names(schema=schema)
    finally:
        if should_close:
            conn.close()


def column_exists(
    table_name: str,
    column_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> bool:
    """
    Check if a column exists in a table.

    Args:
        table_name: Name of the table
        column_name: Name of the column
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        True if column exists, False otherwise

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    if not table_exists(
        table_name, engine=engine, connection=connection, schema=schema
    ):
        return False

    conn, should_close = _normalize_connection(engine, connection)
    try:
        inspector = inspect(conn)
        columns = inspector.get_columns(table_name, schema=schema)
        return any(col["name"] == column_name for col in columns)
    finally:
        if should_close:
            conn.close()


def validate_column_exists(
    table_name: str,
    column_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> None:
    """
    Validate that a column exists in a table.

    Args:
        table_name: Name of the table
        column_name: Name of the column
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Raises:
        ValidationError: If column does not exist
        ValueError: If both engine and connection are provided, or neither is provided
    """
    validate_table_exists(
        table_name, engine=engine, connection=connection, schema=schema
    )
    if not column_exists(
        table_name, column_name, engine=engine, connection=connection, schema=schema
    ):
        raise ValidationError(
            f"Column '{column_name}' does not exist in table '{table_name}'"
        )


def index_exists(
    index_name: str,
    table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> bool:
    """
    Check if an index exists on a table.

    Args:
        index_name: Name of the index
        table_name: Name of the table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        True if index exists, False otherwise

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    if not table_exists(
        table_name, engine=engine, connection=connection, schema=schema
    ):
        return False

    conn, should_close = _normalize_connection(engine, connection)
    try:
        inspector = inspect(conn)
        indexes = inspector.get_indexes(table_name, schema=schema)
        return any(idx["name"] == index_name for idx in indexes)
    finally:
        if should_close:
            conn.close()


def get_primary_key_columns(
    table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> List[str]:
    """
    Get the primary key column names for a table.

    Args:
        table_name: Name of the table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        List of primary key column names

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        inspector = inspect(conn)
        pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
        return pk_constraint.get("constrained_columns", [])
    finally:
        if should_close:
            conn.close()


def get_foreign_keys(
    table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get foreign key information for a table.

    Args:
        table_name: Name of the table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        List of foreign key dictionaries

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        inspector = inspect(conn)
        fks = inspector.get_foreign_keys(table_name, schema=schema)
        # Cast to the expected type
        return fks  # type: ignore[return-value]
    finally:
        if should_close:
            conn.close()


def supports_foreign_keys(
    engine: Optional[Engine] = None, connection: Optional[Connection] = None
) -> bool:
    """
    Check if the database supports foreign keys.

    Args:
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)

    Returns:
        True if foreign keys are supported

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided
    """
    # SQLite with older versions may not support foreign keys
    if is_sqlite(engine=engine, connection=connection):
        conn, should_close = _normalize_connection(engine, connection)
        try:
            result = conn.execute(sql_text("PRAGMA foreign_keys"))
            row = result.fetchone()
            return row[0] == 1 if row else False
        finally:
            if should_close:
                conn.close()
    return True


def _get_table_with_connection(
    table_name: str, connection: Connection, schema: Optional[str] = None
) -> Table:  # type: ignore[return-value]
    """
    Get table using connection (fullmetalalchemy supports connection directly).

    Args:
        table_name: Name of the table
        connection: SQLAlchemy Connection instance
        schema: Optional schema name

    Returns:
        SQLAlchemy Table object
    """
    from fullmetalalchemy.features import get_table

    # fullmetalalchemy.get_table() supports connection directly
    return get_table(table_name, connection, schema=schema)


def _normalize_string_type(
    dtype: Any, dialect: Any, default_varchar_length: Optional[int] = None
) -> Any:
    """
    Normalize String type to database-specific defaults.

    Args:
        dtype: Python str type or SQLAlchemy String instance
        dialect: Database dialect from connection or engine
        default_varchar_length: Explicit default length (overrides dialect defaults)

    Returns:
        Normalized SQLAlchemy String type with appropriate length, or original dtype

    Note:
        - Only normalizes Python str type
        - MySQL requires VARCHAR length (defaults to 255 if not specified)
        - PostgreSQL allows VARCHAR without length
        - SQLAlchemy String instances are returned as-is
    """
    from sqlalchemy.types import String

    # If it's already a SQLAlchemy type instance, return as-is
    # fullmetalalchemy.sql_type can handle String instances directly
    if isinstance(dtype, String):
        # If it has length, return as-is
        if dtype.length is not None:
            return dtype
        # If no length, apply dialect-specific defaults
        dialect_name = dialect.name if hasattr(dialect, "name") else str(dialect)
        if dialect_name == "mysql":
            length = (
                default_varchar_length if default_varchar_length is not None else 255
            )
            return String(length)
        # For other dialects, String() without length is acceptable
        return dtype

    # Check if it's Python str type
    is_str_type = dtype is str or (isinstance(dtype, type) and issubclass(dtype, str))

    if not is_str_type:
        # Not a string type, return as-is (will be converted by sql_type later)
        return dtype

    # Apply dialect-specific defaults for Python str type
    # Note: sql_type(str) converts to String(), but we want to control the length
    dialect_name = dialect.name if hasattr(dialect, "name") else str(dialect)

    if dialect_name == "mysql":
        # MySQL requires VARCHAR length - return String instance with length
        length = default_varchar_length if default_varchar_length is not None else 255
        return String(length)
    elif dialect_name == "postgresql":
        # PostgreSQL allows VARCHAR without length - return str to let sql_type handle it
        # Or if length specified, return String(length)
        if default_varchar_length is not None:
            return String(default_varchar_length)
        # Return str - sql_type will convert to String() which PostgreSQL accepts
        return str
    else:
        # Other databases (e.g., SQLite) - if length specified, return String instance
        # Otherwise return str to let sql_type handle it
        if default_varchar_length is not None:
            # Return String instance - will be used directly without sql_type conversion
            return String(default_varchar_length)
        # Return str - sql_type will handle conversion
        return str


def _commit_if_needed(
    connection: Connection,
    should_close: bool,
    was_in_transaction: Optional[bool] = None,
) -> None:
    """
    Commit a connection if transmutation created it and it needs a commit.

    This helper function enforces the principle that transmutation should only
    commit transactions for connections it creates. User-provided connections
    should never have their transactions committed by transmutation.

    Args:
        connection: SQLAlchemy connection
        should_close: True if transmutation created the connection (via _normalize_connection)
        was_in_transaction: Optional, if provided, indicates whether connection was in
            a transaction before the operation. Used for batch operations that may
            start transactions. If None, checks current state for simple operations.

    Only commits when:
    - should_close=True (transmutation created the connection)
    - For simple operations (was_in_transaction=None): commit if not in transaction
    - For batch operations: commit if not in transaction before OR if in transaction after

    Never commits when should_close=False (user manages their own transactions).
    """
    if not should_close:
        # User provided the connection - never commit, user manages transactions
        return

    # Transmutation created the connection - commit if needed
    if was_in_transaction is None:
        # Simple operation: commit if not in a transaction
        if not connection.in_transaction():
            connection.commit()
    else:
        # Batch operation: commit if we weren't in a transaction before, or if we are now
        # This handles cases where batch_alter_table starts a transaction
        if not was_in_transaction or connection.in_transaction():
            connection.commit()


@contextmanager
def transaction_context(
    engine: Optional[Engine] = None, connection: Optional[Connection] = None
):
    """
    Context manager for database transactions with automatic rollback on error.

    Args:
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)

    Yields:
        Connection object

    Raises:
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> with transaction_context(engine=engine) as conn:
        ...     conn.execute("INSERT INTO table VALUES (1, 'value')")
        >>> with transaction_context(connection=existing_conn) as conn:
        ...     conn.execute("INSERT INTO table VALUES (1, 'value')")
    """
    conn, should_close = _normalize_connection(engine, connection)
    trans = conn.begin()
    try:
        yield conn
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        if should_close:
            conn.close()
