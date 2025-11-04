"""Constraint operations for database schema modifications."""

from typing import List, Optional, Union, Sequence

from sqlalchemy import Table
from sqlalchemy.engine import Engine, Connection

from fullmetalalchemy.features import get_primary_key_constraints

from transmutation.utils import (
    _get_op,
    _normalize_connection,
    _get_table_with_connection,
    _commit_if_needed,
    validate_table_exists,
    validate_column_exists,
    supports_foreign_keys,
)
from transmutation.exceptions import ConstraintError, ValidationError


def create_foreign_key(
    constraint_name: str,
    source_table: str,
    source_columns: Union[str, List[str]],
    referent_table: str,
    referent_columns: Union[str, List[str]],
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
    onupdate: Optional[str] = None,
    ondelete: Optional[str] = None,
    deferrable: Optional[bool] = None,
    initially: Optional[str] = None,
) -> Table:
    """
    Create a foreign key constraint.

    Args:
        constraint_name: Name of the foreign key constraint
        source_table: Name of the table with the foreign key
        source_columns: Column(s) in the source table
        referent_table: Name of the referenced table
        referent_columns: Column(s) in the referenced table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name
        onupdate: Action on update (CASCADE, SET NULL, etc.)
        ondelete: Action on delete (CASCADE, SET NULL, etc.)
        deferrable: Whether the constraint is deferrable
        initially: When to check constraint (DEFERRED, IMMEDIATE)

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ConstraintError: If the create operation fails
        ValidationError: If tables or columns don't exist

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = create_foreign_key(
        ...     'fk_user_address',
        ...     'addresses',
        ...     'user_id',
        ...     'users',
        ...     'id',
        ...     engine,
        ...     ondelete='CASCADE'
        ... )
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        if not supports_foreign_keys(connection=conn):
            raise ConstraintError(
                "Foreign keys are not supported or not enabled on this database"
            )

        validate_table_exists(source_table, connection=conn, schema=schema)
        validate_table_exists(referent_table, connection=conn, schema=schema)

        # Normalize to lists
        if isinstance(source_columns, str):
            source_columns = [source_columns]
        if isinstance(referent_columns, str):
            referent_columns = [referent_columns]

        # Validate columns
        for col in source_columns:
            validate_column_exists(source_table, col, connection=conn, schema=schema)
        for col in referent_columns:
            validate_column_exists(referent_table, col, connection=conn, schema=schema)

        if len(source_columns) != len(referent_columns):
            raise ValidationError(
                "Source and referent columns must have the same length"
            )

        op = _get_op(connection=conn)

        # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
        was_in_transaction = conn.in_transaction()
        with op.batch_alter_table(source_table, schema=schema) as batch_op:
            batch_op.create_foreign_key(
                constraint_name,
                referent_table,
                source_columns,
                referent_columns,
                onupdate=onupdate,
                ondelete=ondelete,
                deferrable=deferrable,
                initially=initially,
            )  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
        # If connection was provided by user, they manage commits
        _commit_if_needed(conn, should_close, was_in_transaction)

        return _get_table_with_connection(source_table, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and (
            "ValidationError" in e.__class__.__name__
            or "ConstraintError" in e.__class__.__name__
        ):
            raise
        raise ConstraintError(
            f"Failed to create foreign key '{constraint_name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()


def drop_constraint(
    constraint_name: str,
    table_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    type_: str = "foreignkey",
    schema: Optional[str] = None,
) -> Table:
    """
    Drop a constraint from a table.

    Args:
        constraint_name: Name of the constraint to drop
        table_name: Name of the table
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        type_: Type of constraint ('foreignkey', 'unique', 'check', 'primary')
        schema: Optional schema name

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ConstraintError: If the drop operation fails
        ValidationError: If the table doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = drop_constraint('fk_user_address', 'addresses', engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)

        op = _get_op(connection=conn)

        # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
        was_in_transaction = conn.in_transaction()
        with op.batch_alter_table(table_name, schema=schema) as batch_op:
            batch_op.drop_constraint(constraint_name, type_=type_)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
        # If connection was provided by user, they manage commits
        _commit_if_needed(conn, should_close, was_in_transaction)

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise ConstraintError(
            f"Failed to drop constraint '{constraint_name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()


def create_unique_constraint(
    constraint_name: str,
    table_name: str,
    columns: Union[str, List[str]],
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> Table:
    """
    Create a unique constraint on one or more columns.

    Args:
        constraint_name: Name of the unique constraint
        table_name: Name of the table
        columns: Column name or list of column names
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ConstraintError: If the create operation fails
        ValidationError: If the table or columns don't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = create_unique_constraint('uq_email', 'users', 'email', engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)

        # Normalize to list
        if isinstance(columns, str):
            columns = [columns]

        # Validate columns
        for col in columns:
            validate_column_exists(table_name, col, connection=conn, schema=schema)

        op = _get_op(connection=conn)

        # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
        was_in_transaction = conn.in_transaction()
        with op.batch_alter_table(table_name, schema=schema) as batch_op:
            batch_op.create_unique_constraint(constraint_name, columns)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
        # If connection was provided by user, they manage commits
        _commit_if_needed(conn, should_close, was_in_transaction)

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise ConstraintError(
            f"Failed to create unique constraint '{constraint_name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()


def create_check_constraint(
    constraint_name: str,
    table_name: str,
    condition: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> Table:
    """
    Create a check constraint on a table.

    Args:
        constraint_name: Name of the check constraint
        table_name: Name of the table
        condition: SQL condition for the check constraint
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ConstraintError: If the create operation fails
        ValidationError: If the table doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = create_check_constraint(
        ...     'ck_age_positive',
        ...     'users',
        ...     'age > 0',
        ...     engine
        ... )
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)

        op = _get_op(connection=conn)

        # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
        was_in_transaction = conn.in_transaction()
        with op.batch_alter_table(table_name, schema=schema) as batch_op:
            batch_op.create_check_constraint(constraint_name, condition)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
        # If connection was provided by user, they manage commits
        _commit_if_needed(conn, should_close, was_in_transaction)

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise ConstraintError(
            f"Failed to create check constraint '{constraint_name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()


def create_primary_key(
    table_name: str,
    column_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> Table:
    """
    Add a primary key constraint to a table.

    Only use on a table with no primary key.
    Use replace_primary_key on tables with an existing primary key.

    Args:
        table_name: Name of the table
        column_name: Name of the column to make primary key
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ConstraintError: If the create operation fails
        ValidationError: If the table or column doesn't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = create_primary_key('users', 'id', engine)
    """
    return create_primary_keys(table_name, [column_name], engine, connection, schema)


def create_primary_keys(
    table_name: str,
    column_names: Sequence[str],
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> Table:
    """
    Add a composite primary key constraint to a table.

    Only use on a table with no primary key.
    Use replace_primary_keys on tables with an existing primary key.

    Args:
        table_name: Name of the table
        column_names: Names of the columns to make primary key
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ConstraintError: If the create operation fails
        ValidationError: If the table or columns don't exist
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = create_primary_keys('user_roles', ['user_id', 'role_id'], engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        validate_table_exists(table_name, connection=conn, schema=schema)

        # Validate columns
        for col in column_names:
            validate_column_exists(table_name, col, connection=conn, schema=schema)

        op = _get_op(connection=conn)
        constraint_name = f"pk_{table_name}"

        # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
        was_in_transaction = conn.in_transaction()
        with op.batch_alter_table(table_name, schema=schema) as batch_op:
            batch_op.create_unique_constraint(constraint_name, column_names)  # type: ignore
            batch_op.create_primary_key(constraint_name, column_names)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
        # If connection was provided by user, they manage commits
        _commit_if_needed(conn, should_close, was_in_transaction)

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        if hasattr(e, "__class__") and "ValidationError" in e.__class__.__name__:
            raise
        raise ConstraintError(
            f"Failed to create primary key on '{table_name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()


def replace_primary_key(
    table: Table,
    column_name: str,
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> Table:
    """
    Replace the primary key of a table with a new column.

    Args:
        table: SQLAlchemy Table object
        column_name: Name of the column to make primary key
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ConstraintError: If the replace operation fails
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> from fullmetalalchemy.features import get_table
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = get_table('users', engine)
        >>> table = replace_primary_key(table, 'uuid', engine)
    """
    return replace_primary_keys(table, [column_name], engine, connection, schema)


def replace_primary_keys(
    table: Table,
    column_names: Sequence[str],
    engine: Optional[Engine] = None,
    connection: Optional[Connection] = None,
    schema: Optional[str] = None,
) -> Table:
    """
    Replace the primary key of a table with new columns (composite key).

    Args:
        table: SQLAlchemy Table object
        column_names: Names of the columns to make primary key
        engine: SQLAlchemy Engine instance (mutually exclusive with connection)
        connection: SQLAlchemy Connection instance (mutually exclusive with engine)
        schema: Optional schema name

    Returns:
        Newly reflected SQLAlchemy Table object

    Raises:
        ConstraintError: If the replace operation fails
        ValueError: If both engine and connection are provided, or neither is provided

    Example:
        >>> from sqlalchemy import create_engine
        >>> from fullmetalalchemy.features import get_table
        >>> engine = create_engine('sqlite:///test.db')
        >>> table = get_table('user_roles', engine)
        >>> table = replace_primary_keys(table, ['user_id', 'role_id'], engine)
    """
    conn, should_close = _normalize_connection(engine, connection)
    try:
        table_name = table.name
        op = _get_op(connection=conn)
        keys = get_primary_key_constraints(table)

        # batch_alter_table may require a commit even if not in a transaction (e.g., SQLite)
        was_in_transaction = conn.in_transaction()
        with op.batch_alter_table(table_name, schema=schema) as batch_op:
            # Name primary key constraint if not named (sqlite)
            constraint_name_from_keys = keys[0] if keys else None
            pk_columns = keys[1] if len(keys) > 1 else []

            if constraint_name_from_keys is None:
                constraint_name = f"pk_{table_name}"
                batch_op.create_primary_key(constraint_name, pk_columns)  # type: ignore
            else:
                constraint_name = constraint_name_from_keys

            batch_op.drop_constraint(constraint_name, type_="primary")  # type: ignore
            batch_op.create_unique_constraint(constraint_name, column_names)  # type: ignore
            batch_op.create_primary_key(constraint_name, column_names)  # type: ignore
        # Commit if transmutation created the connection and it needs a commit
        # Note: Some databases (e.g., SQLite) require commit even when not in explicit transaction
        # If connection was provided by user, they manage commits
        _commit_if_needed(conn, should_close, was_in_transaction)

        return _get_table_with_connection(table_name, conn, schema)
    except Exception as e:
        raise ConstraintError(
            f"Failed to replace primary key on '{table.name}': {str(e)}"
        ) from e
    finally:
        if should_close:
            conn.close()
