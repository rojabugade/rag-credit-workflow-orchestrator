from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from creditflow.auth.principal import Principal
from creditflow.core.config import Settings, get_settings
from creditflow.core.errors import AuthorizationError

bearer = HTTPBearer(auto_error=False)
LOCAL_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


async def get_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
    x_local_roles: Annotated[str, Header()] = "analyst,policy_admin",
) -> Principal:
    if settings.local_auth_enabled and settings.env in {"local", "test"}:
        return Principal(
            "local-analyst", LOCAL_TENANT_ID, frozenset(x.strip() for x in x_local_roles.split(","))
        )
    if credentials is None or not settings.oidc_issuer or not settings.oidc_jwks_url:
        raise AuthorizationError("bearer authentication is required")
    try:
        jwks = jwt.PyJWKClient(settings.oidc_jwks_url)
        signing_key = jwks.get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
        tenant_id = UUID(claims["tenant_id"])
        roles = frozenset(claims.get("roles", []))
        return Principal(claims["sub"], tenant_id, roles)
    except (jwt.PyJWTError, ValueError) as exc:
        raise AuthorizationError("token validation failed") from exc
