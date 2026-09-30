from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from app.config import Settings, get_settings


@dataclass(frozen=True)
class User:
    email: str
    roles: frozenset[str]


def get_current_user(request: Request, settings: Settings = Depends(get_settings)) -> User:
    # Identity headers are injected by the corporate SSO proxy, which strips any
    # client-supplied copies. Only trust them behind that proxy.
    email = request.headers.get("X-Forwarded-Email")
    if email:
        groups = request.headers.get("X-Forwarded-Groups", "")
        return User(email=email, roles=frozenset(g.strip() for g in groups.split(",") if g.strip()))
    if settings.env == "dev" and settings.dev_user:
        return User(email=settings.dev_user, roles=settings.dev_roles)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def require_role(role: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if role not in user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency


require_reader = require_role("wellops.reader")
