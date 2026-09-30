import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    env: str
    db_path: str
    dev_user: str | None
    dev_roles: frozenset[str]
    log_level: str


@lru_cache
def get_settings() -> Settings:
    env = os.environ.get("WELL_OPS_ENV", "dev")
    roles = os.environ.get("WELL_OPS_DEV_ROLES", "wellops.reader")
    return Settings(
        env=env,
        db_path=os.environ.get("WELL_OPS_DB_PATH", "data/wells.db"),
        dev_user=os.environ.get("WELL_OPS_DEV_USER", "dev@example.com") if env == "dev" else None,
        dev_roles=frozenset(r.strip() for r in roles.split(",") if r.strip()),
        log_level=os.environ.get("WELL_OPS_LOG_LEVEL", "INFO"),
    )
