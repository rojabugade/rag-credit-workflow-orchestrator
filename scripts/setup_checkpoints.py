"""Initialize LangGraph's PostgreSQL checkpoint tables during deployment migration."""

import asyncio

from creditflow.core.config import get_settings
from creditflow.workflows.checkpoints import postgres_checkpointer


async def main() -> None:
    connection_string = get_settings().checkpoint_database_url
    if not connection_string:
        raise ValueError("CREDITFLOW_CHECKPOINT_DATABASE_URL is required")
    async with postgres_checkpointer(connection_string, setup=True):
        pass


if __name__ == "__main__":
    asyncio.run(main())
