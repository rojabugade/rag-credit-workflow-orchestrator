from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


@asynccontextmanager
async def postgres_checkpointer(
    connection_string: str, *, setup: bool = False
) -> AsyncIterator[AsyncPostgresSaver]:
    """Create the durable production saver; setup is reserved for migration/admin jobs."""
    async with AsyncPostgresSaver.from_conn_string(connection_string) as saver:
        if setup:
            await saver.setup()
        yield saver
