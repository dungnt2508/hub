"""
Utilities for database session / transaction handling.
Tránh lỗi "A transaction is already begun" khi session đã nằm trong transaction (vd: test fixtures).
"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transaction_scope(session: AsyncSession):
    """
    Context manager cho transaction. Dùng begin_nested() nếu đã có transaction
    (savepoint), ngược lại dùng begin(). Tránh lỗi "A transaction is already begun".
    """
    if session.sync_session.in_transaction():
        async with session.begin_nested():
            yield
    else:
        async with session.begin():
            yield
