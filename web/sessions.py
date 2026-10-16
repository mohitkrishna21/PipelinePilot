import os
import shutil
import tempfile
import time
import asyncio
import uuid

from dataclasses import dataclass, field
from agents import Agent, SQLiteSession
from agents.mcp import MCPServerStdio
from agent_sdk.agents import build_pipeline_assistant


@dataclass
class Session:
    session_id: str
    db_path: str
    agent: Agent
    chat: SQLiteSession
    closed: asyncio.Event
    task: asyncio.Task
    last_used: float
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    turns: int = 0


class DemoFull(Exception):
    pass


def copy_demo_db(source_path: str, session_id: str) -> str:
    folder = os.path.join(
        tempfile.gettempdir(),
        "pipelinepilot"
    )

    os.makedirs(folder, exist_ok=True)

    dest = os.path.join(folder, f"{session_id}.db")

    shutil.copyfile(source_path, dest)

    return dest


async def _session_worker(
    settings,
    session_id,
    db_path,
    ready,
    closed
):
    params = {
        "command": settings.server_python,
        "args": ["server/pipeline_server.py"],
        "env": {"DB_PATH": db_path}
    }

    try:
        async with MCPServerStdio(
            name="pipeline",
            params=params,
            cache_tools_list=True,
            client_session_timeout_seconds=30,
            require_approval={
                "always": {
                    "tool_names": ["mark_followed_up"]
                }
            }
        ) as server:

            agent = build_pipeline_assistant(server)
            chat = SQLiteSession(session_id)

            ready.set_result((agent, chat))

            await closed.wait()

    except Exception as exc:
        if not ready.done():
            ready.set_exception(exc)


async def open_session(settings, session_id: str) -> Session:
    db_path = copy_demo_db(settings.db_path, session_id)

    loop = asyncio.get_running_loop()
    ready = loop.create_future()
    closed = asyncio.Event()

    task = asyncio.create_task(
        _session_worker(
            settings,
            session_id,
            db_path,
            ready,
            closed
        )
    )

    try:
        agent, chat = await ready

    except Exception:
        await task

        try:
            os.remove(db_path)
        except FileNotFoundError:
            pass

        raise

    return Session(
        session_id=session_id,
        db_path=db_path,
        agent=agent,
        chat=chat,
        closed=closed,
        task=task,
        last_used=time.time()
    )


async def close_session(session: Session) -> None:
    session.closed.set()

    await session.task

    try:
        os.remove(session.db_path)
    except FileNotFoundError:
        pass


async def get_or_open_session(
    settings,
    sessions,
    session_id
) -> Session:

    # Reuse an existing session
    if session_id is not None and session_id in sessions:
        s = sessions[session_id]
        s.last_used = time.time()
        return s

    # Enforce maximum session capacity
    if len(sessions) >= settings.max_sessions:
        raise DemoFull

    # Create a new session
    new_id = uuid.uuid4().hex

    session = await open_session(settings, new_id)

    sessions[new_id] = session

    return session


async def reap_idle_sessions(settings, sessions) -> int:
    now = time.time()
    ttl = settings.session_ttl_minutes * 60

    stale = [
        sid
        for sid, s in sessions.items()
        if now - s.last_used > ttl and not s.lock.locked()
    ]

    for sid in stale:
        s = sessions.pop(sid)
        await close_session(s)

    return len(stale)


async def reaper_loop(
    settings,
    sessions,
    interval_seconds=60
):
    while True:
        await asyncio.sleep(interval_seconds)

        try:
            await reap_idle_sessions(settings, sessions)

        except Exception as exc:
            print(f"Session reaper error: {exc}")


async def close_all_sessions(sessions) -> None:
    for sid in list(sessions.keys()):
        s = sessions.pop(sid)
        await close_session(s)
