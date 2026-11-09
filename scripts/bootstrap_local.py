"""Create only the fixed synthetic local tenant and development identities."""

import asyncio
from uuid import UUID

from sqlalchemy import select, text

from creditflow.db.models.entities import Tenant, User, UserRole
from creditflow.db.session import session_factory

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


async def main() -> None:
    async with session_factory.begin() as session:
        tenant = await session.get(Tenant, TENANT_ID)
        if tenant is None:
            tenant = Tenant(id=TENANT_ID, name="Synthetic Local Bank", status="ACTIVE")
            session.add(tenant)
            await session.flush()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(TENANT_ID)},
        )
        user = await session.scalar(
            select(User).where(User.tenant_id == TENANT_ID, User.subject == "local-analyst")
        )
        if user is None:
            user = User(
                tenant_id=TENANT_ID,
                subject="local-analyst",
                email="local-analyst@example.invalid",
                active=True,
            )
            session.add(user)
            await session.flush()
        existing = set(
            (await session.scalars(select(UserRole.role).where(UserRole.user_id == user.id))).all()
        )
        for role in {"analyst", "underwriter", "manager", "policy_admin"} - existing:
            session.add(UserRole(tenant_id=TENANT_ID, user_id=user.id, role=role))


if __name__ == "__main__":
    asyncio.run(main())
