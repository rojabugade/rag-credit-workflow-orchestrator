from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: UUID
    roles: frozenset[str]

    def require(self, *allowed: str) -> None:
        if not self.roles.intersection(allowed):
            from creditflow.core.errors import AuthorizationError

            raise AuthorizationError("the authenticated principal lacks the required role")
