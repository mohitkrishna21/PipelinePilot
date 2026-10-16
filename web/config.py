import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    demo_mode: bool
    db_path: str
    server_python: str
    max_turns: int
    rate_limit_per_min: int
    max_body_bytes: int
    session_ttl_minutes: int
    max_sessions: int
    openai_timeout_seconds: int
    openai_max_retries: int
    turn_timeout_seconds: int
    max_turns_per_session: int


def load_settings() -> Settings:
    db_path = os.environ.get("DB_PATH", "db/demo_pipeline.db")
    server_python = os.environ.get("SERVER_PYTHON", sys.executable)

    max_turns = int(os.environ.get("MAX_TURNS", "8"))
    rate_limit_per_min = int(os.environ.get("RATE_LIMIT_PER_MIN", "20"))
    max_body_bytes = int(os.environ.get("MAX_BODY_BYTES", "20000"))
    session_ttl_minutes = int(os.environ.get("SESSION_TTL_MINUTES", "30"))
    max_sessions = int(os.environ.get("MAX_SESSIONS", "5"))

    openai_timeout_seconds = int(
        os.environ.get("OPENAI_TIMEOUT_SECONDS", "30")
    )

    openai_max_retries = int(
        os.environ.get("OPENAI_MAX_RETRIES", "3")
    )

    turn_timeout_seconds = int(
        os.environ.get("TURN_TIMEOUT_SECONDS", "180")
    )

    max_turns_per_session = int(
        os.environ.get("MAX_TURNS_PER_SESSION", "20")
    )

    demo_mode = os.environ.get("DEMO_MODE", "0").lower() in (
        "1", "true", "yes"
    )

    return Settings(
        demo_mode=demo_mode,
        db_path=db_path,
        server_python=server_python,
        max_turns=max_turns,
        rate_limit_per_min=rate_limit_per_min,
        max_body_bytes=max_body_bytes,
        session_ttl_minutes=session_ttl_minutes,
        max_sessions=max_sessions,
        openai_timeout_seconds=openai_timeout_seconds,
        openai_max_retries=openai_max_retries,
        turn_timeout_seconds=turn_timeout_seconds,
        max_turns_per_session=max_turns_per_session
    )


def validate_demo_config(settings: Settings) -> None:
    if not settings.demo_mode:
        return

    if not os.path.exists(settings.db_path):
        raise RuntimeError(
            f"DEMO_MODE: database not found: {settings.db_path}"
        )

    name = os.path.basename(settings.db_path).lower()

    if "demo" not in name:
        raise RuntimeError(
            "DEMO_MODE requires a demo database "
            "(file name must contain 'demo')."
        )

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "DEMO_MODE: OPENAI_API_KEY is missing."
        )
