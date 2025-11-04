"""Column operations for database schema modifications."""

from typing import Any, Optional, Union

from sqlalchemy import Table, Column, inspect
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.types import TypeEngine

from fullmetalalchemy.type_convert import sql_type

from transmutation.utils import (
    _get_op,
    _normalize_connection,
    _get_table_with_connection,
    _normalize_string_type,
    _commit_if_needed,
    validate_table_exists,
    validate_column_exists,
)
from transmutation.exceptions import ColumnError


def rename_column(
    table_name: str,
    old_col_name: str,
    new_col_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    existing_type: Optional[Union[type, TypeEngine[Any]]] = None,
    verify: bool = False,
) -> Table:
    """
    Rename a table column.

    Args:
        table_name: Name of the table containing the column
        old_col_name: Current name of the column
        new_col_name: New name for the column
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        existing_type: Existing column type (auto-detected for MySQL if not provided)
            Required for MySQL if auto-detection fails
        verify: If True, verify column was renamed using inspect() (default: False)
            Setting to False avoids metadata lock issues in PostgreSQL

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ColumnError: If the rename operation fails
        ValidationError: If the table or column doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = rename_column('users', 'name', 'full_name', engine)
        >>> # MySQL with auto-detected type:
        >>> table = rename_column('users', 'name', 'full_name', engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)
        validate_column_exists(table_name, old_col_name, connection=conn, schema=schema)

        # MySQL-specific handling: auto-detect existing type if not provided
        if conn.dialect.name == "mysql" and existing_type is None:
            inspector = inspect(conn)
            columns_info = inspector.get_columns(table_name, schema=schema)
            column_info = next(
                (col for col in columns_info if col["name"] == old_col_name), None
            )
            if column_info is None:
                raise ColumnError(
                    f"Column '{old_col_name}' not found in table '{table_name}'"
                )
            existing_type = column_info["type"]

        op = _get_op(connection=conn)

        if conn.dialect.name == "mysql" and existing_type is not None:
            # MySQL requires CHANGE COLUMN with type
            # Use raw SQL for MySQL-specific syntax
            from sqlalchemy import text

            # Type checking: existing_type could be type or TypeEngine
            if isinstance(existing_type, TypeEngine):
                type_str = str(existing_type.compile(dialect=conn.dialect))
            else:
                # If it's a Python type, convert it first
                sa_type = sql_type(existing_type)
                type_str = str(sa_type.compile(dialect=conn.dialect))
            table_ref = f"{schema}.{table_name}" if schema else table_name
            sql = f"ALTER TABLE {table_ref} CHANGE COLUMN `{old_col_name}` `{new_col_name}` {type_str}"
            conn.execute(text(sql))
            # Commit if transmutation created the connection and it needs a commit
            _commit_if_needed(conn, should_close)
        else:
            # Standard SQLAlchemy batch operation for other databases
            # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
            was_in_transaction = conn.in_transaction()
            try:
                with op.batch_alter_table(table_name, schema=schema) as batch_op:
                    batch_op.alter_column(
                        old_col_name, nullable=True, new_column_name=new_col_name
                    )  # type: ignore
            except Exception as batch_error:
                # Handle SQLAlchemy DuplicateColumnError that occurs during batch operation
                from sqlalchemy.exc import DuplicateColumnError

                if isinstance(batch_error, DuplicateColumnError):
                    raise ColumnError(
                        f"Failed to rename column '{old_col_name}' to '{new_col_name}': {str(batch_error)}"
                    ) from batch_error
                raise
            # Commit if transmutation created the connection and it needs a commit
            # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
            # If connection was provided by user, they manage commits
            _commit_if_needed(conn, should_close, was_in_transaction)

        # Only verify if explicitly requested
        if verify:
            inspector = inspect(conn)
            columns = inspector.get_columns(table_name, schema=schema)
            if not any(col["name"] == new_col_name for col in columns):
                raise ColumnError(
                    f"Column '{new_col_name}' was not found after rename operation"
                )
            if any(col["name"] == old_col_name for col in columns):
                raise ColumnError(
                    f"Column '{old_col_name}' still exists after rename operation"
                )

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        if hasattr(e, "__class__") and "ColumnError" in e.__class__.__name__:
            raise
        # Handle SQLAlchemy DuplicateColumnError
        from sqlalchemy.exc import DuplicateColumnError

        if isinstance(e, DuplicateColumnError):
            raise ColumnError(
                f"Failed to rename column '{old_col_name}': {str(e)}"
            ) from e
        raise ColumnError(f"Failed to rename column '{old_col_name}': {str(e)}") from e
    finally:
        if should_close:
            conn.close()


def drop_column(
    table_name: str,
    col_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    verify: bool = False,
) -> Table:
    """
    Drop a column from a table.

    Args:
        table_name: Name of the table
        col_name: Name of the column to drop
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        verify: If True, verify column was dropped using inspect() (default: False)
            Setting to False avoids metadata lock issues in PostgreSQL

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ColumnError: If the drop operation fails
        ValidationError: If the table or column doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = drop_column('users', 'middle_name', engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)
        validate_column_exists(table_name, col_name, connection=conn, schema=schema)

        op = _get_op(connection=conn)

        # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
        was_in_transaction = conn.in_transaction()
        with op.batch_alter_table(table_name, schema=schema) as batch_op:
            batch_op.drop_column(col_name)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
        # If connection was provided by user, they manage commits
        _commit_if_needed(conn, should_close, was_in_transaction)

        # Only verify if explicitly requested
        if verify:
            inspector = inspect(conn)
            columns = inspector.get_columns(table_name, schema=schema)
            if any(col["name"] == col_name for col in columns):
                raise ColumnError(
                    f"Column '{col_name}' still exists after drop operation"
                )

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise ColumnError(f"Failed to drop column '{col_name}': {str(e)}") from e
    finally:
        if should_close:
            conn.close()


def add_column(
    table_name: str,
    column_name: str,
    dtype: Any,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    nullable: bool = True,
    default: Optional[Any] = None,
    server_default: Optional[Any] = None,
    verify: bool = False,
    default_varchar_length: Optional[int] = None,
) -> Table:
    """
    Add a column to a table.

    Args:
        table_name: Name of the table
        column_name: Name of the new column
        dtype: Data type for the column (Python type or SQLAlchemy type)
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        nullable: Whether the column allows NULL values (default: True)
        default: Python-side default value
        server_default: Server-side default value
        verify: If True, verify column was added using inspect() (default: False)
            Setting to False avoids metadata lock issues in PostgreSQL
        default_varchar_length: Default length for VARCHAR columns
            - MySQL: defaults to 255 if not provided
            - PostgreSQL: ignored (VARCHAR without length allowed)
            - Other databases: uses provided length or allows no length

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ColumnError: If the add operation fails
        ValidationError: If the table doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = add_column('users', 'email', str, engine, nullable=False)
        >>> # With connection for transaction safety:
        >>> with engine.begin() as conn:
        ...     table = add_column('users', 'email', str, connection=conn)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)

        # Normalize string types for database-specific defaults
        normalized_dtype = _normalize_string_type(
            dtype, conn.dialect, default_varchar_length=default_varchar_length
        )

        # If normalized_dtype is already a SQLAlchemy type instance, use it directly
        # Otherwise, convert using sql_type
        if isinstance(normalized_dtype, TypeEngine):
            sa_type = normalized_dtype
        else:
            sa_type = sql_type(normalized_dtype)
        op = _get_op(connection=conn)

        col: Column[Any] = Column(
            column_name,
            sa_type,
            nullable=nullable,
            default=default,
            server_default=server_default,
        )

        op.add_column(table_name, col, schema=schema)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        _commit_if_needed(conn, should_close)

        # Only verify if explicitly requested (prevents metadata locks)
        if verify:
            inspector = inspect(conn)
            columns = inspector.get_columns(table_name, schema=schema)
            if not any(col["name"] == column_name for col in columns):
                raise ColumnError(
                    f"Column '{column_name}' was not found after add operation"
                )

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise ColumnError(f"Failed to add column '{column_name}': {str(e)}") from e
    finally:
        if should_close:
            conn.close()


def alter_column(
    table_name: str,
    column_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    new_column_name: Optional[str] = None,
    type_: Optional[Union[type, TypeEngine[Any]]] = None,
    nullable: Optional[bool] = None,
    default: Optional[Any] = None,
    server_default: Optional[Any] = None,
    comment: Optional[str] = None,
    verify: bool = False,
) -> Table:
    """
    Alter various properties of a column.

    Args:
        table_name: Name of the table
        column_name: Name of the column to alter
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        new_column_name: New name for the column (if renaming)
        type_: New data type for the column
        nullable: New nullable setting
        default: New Python-side default value
        server_default: New server-side default value
        comment: New column comment
        verify: If True, verify column was altered using inspect() (default: False)
            Setting to False avoids metadata lock issues in PostgreSQL

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ColumnError: If the alter operation fails
        ValidationError: If the table or column doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = alter_column('users', 'age', engine, nullable=False, default=0)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)
        validate_column_exists(table_name, column_name, connection=conn, schema=schema)

        op = _get_op(connection=conn)

        # Convert Python type to SQLAlchemy type if needed
        converted_type: Optional[TypeEngine[Any]] = None
        if type_ is not None and not isinstance(type_, TypeEngine):
            converted_type = sql_type(type_)
        elif type_ is not None:
            converted_type = type_  # type: ignore

        # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
        was_in_transaction = conn.in_transaction()
        with op.batch_alter_table(table_name, schema=schema) as batch_op:
            batch_op.alter_column(
                column_name,
                new_column_name=new_column_name,
                type_=converted_type,
                nullable=nullable,
                server_default=server_default,
                comment=comment,
            )  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
        # If connection was provided by user, they manage commits
        _commit_if_needed(conn, should_close, was_in_transaction)

        # Only verify if explicitly requested
        if verify:
            inspector = inspect(conn)
            columns = inspector.get_columns(table_name, schema=schema)
            final_name = new_column_name if new_column_name else column_name
            if not any(col["name"] == final_name for col in columns):
                raise ColumnError(
                    f"Column '{final_name}' was not found after alter operation"
                )

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise ColumnError(f"Failed to alter column '{column_name}': {str(e)}") from e
    finally:
        if should_close:
            conn.close()
