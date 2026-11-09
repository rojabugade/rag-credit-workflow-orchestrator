from typing import Annotated, cast

from fastapi import Depends

from creditflow.core.config import Settings, get_settings
from creditflow.services.contracts import UnderwritingRuntime
from creditflow.services.runtime import runtime

_postgres_runtime: UnderwritingRuntime | None = None


def get_runtime(settings: Annotated[Settings, Depends(get_settings)]) -> UnderwritingRuntime:
    global _postgres_runtime
    if settings.runtime_backend == "local":
        return cast("UnderwritingRuntime", runtime)
    if _postgres_runtime is None:
        from creditflow.services.postgres_runtime import PostgresRuntime

        _postgres_runtime = PostgresRuntime.from_settings(settings)
    return _postgres_runtime


RuntimeDep = Annotated[UnderwritingRuntime, Depends(get_runtime)]
