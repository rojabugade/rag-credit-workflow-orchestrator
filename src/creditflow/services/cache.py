import hashlib
import json
from dataclasses import asdict, dataclass

from redis.asyncio import Redis
from redis.exceptions import RedisError

from creditflow.core.errors import CreditFlowError


@dataclass(frozen=True)
class CacheIdentity:
    tenant_id: str
    operation: str
    source_versions: tuple[str, ...]
    policy_versions: tuple[str, ...]
    prompt_version: str
    model_configuration: str
    payload_hash: str
    schema_version: str = "1"

    def key(self) -> str:
        canonical = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return f"creditflow:{self.tenant_id}:{self.operation}:{hashlib.sha256(canonical.encode()).hexdigest()}"


class TenantCache:
    def __init__(self, redis: Redis, *, ttl_seconds: int = 900) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def get_json(self, identity: CacheIdentity) -> dict[str, object] | None:
        try:
            value = await self.redis.get(identity.key())
            if value is None:
                return None
            parsed = json.loads(value)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except (RedisError, json.JSONDecodeError) as exc:
            raise CreditFlowError("cache read failed") from exc

    async def put_json(self, identity: CacheIdentity, value: dict[str, object]) -> None:
        try:
            await self.redis.set(
                identity.key(), json.dumps(value, separators=(",", ":")), ex=self.ttl_seconds
            )
        except RedisError as exc:
            raise CreditFlowError("cache write failed") from exc
