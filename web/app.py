import asyncio
import time
import traceback
import openai

from collections import deque
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from agent_sdk.service import run_turn
from web.approvals import make_ask_approval, resolve_approval
from web.config import load_settings, validate_demo_config
from web.guards import allow_request, client_ip
from web.logs import log_json
from web.metrics import summarize
from web.pipeline import read_pipeline
from web.resilience import configure_openai, friendly_error
from web.sessions import (
    reaper_loop,
    close_all_sessions,
    close_session,
    get_or_open_session,
    DemoFull,
)
from web.sse import sse


# Load environment variables before settings
load_dotenv()
settings = load_settings()
validate_demo_config(settings)
configure_openai(settings)


# Shared application state
pending = {}
sessions = {}
background_tasks = set()
rate_hits = {}
metrics = deque(maxlen=500)

APPROVAL_TIMEOUT = 120


# Request models
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    session_id: str | None = None


class ApproveRequest(BaseModel):
    session_id: str
    approved: bool


class CloseRequest(BaseModel):
    session_id: str


# Application lifecycle
@asynccontextmanager
async def lifespan(app):
    reaper = asyncio.create_task(
        reaper_loop(settings, sessions)
    )

    try:
        yield

    finally:
        reaper.cancel()

        try:
            await reaper
        except asyncio.CancelledError:
            pass

        await close_all_sessions(sessions)


app = FastAPI(lifespan=lifespan)


# Request body-size middleware
@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    length = request.headers.get("content-length")

    if length is not None:
        try:
            body_size = int(length)

        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Bad request."}
            )

        if body_size > settings.max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request too large."}
            )

    return await call_next(request)


# Health endpoint
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode
    }


# Pipeline endpoint
@app.get("/pipeline")
def pipeline():
    rows = read_pipeline(settings.db_path)

    return {
        "applications": rows,
        "count": len(rows)
    }


# Metrics endpoint
@app.get("/metrics")
def metrics_view():
    return {
        **summarize(metrics),
        "active_sessions": len(sessions),
        "max_sessions": settings.max_sessions
    }


# Approval endpoint
@app.post("/approve")
async def approve(req: ApproveRequest):
    ok = resolve_approval(
        req.session_id,
        req.approved,
        pending
    )

    return {"resolved": ok}


# Close session endpoint
@app.post("/session/close")
async def close_my_session(req: CloseRequest):
    session = sessions.get(req.session_id)

    if session is None:
        return {"closed": False}

    if session.lock.locked():
        return {"closed": False}

    sessions.pop(req.session_id, None)

    await close_session(session)

    log_json(
        "session_closed",
        session=req.session_id[:8]
    )

    return {"closed": True}


# Chat endpoint with SSE streaming
@app.post("/chat")
async def chat(req: ChatRequest, request: Request):

    # 1. Start the clock
    started = time.perf_counter()

    # 2. Check per-IP rate limit
    ip = client_ip(request)

    if not allow_request(
        rate_hits,
        ip,
        settings.rate_limit_per_min,
        time.time()
    ):
        log_json("rejected", reason="rate_limited")

        raise HTTPException(
            status_code=429,
            detail=(
                "Too many requests. Please slow down "
                "and try again in a minute."
            )
        )

    # 3. Get or create session
    try:
        session = await get_or_open_session(
            settings,
            sessions,
            req.session_id
        )

    except DemoFull:
        log_json("rejected", reason="demo_full")

        raise HTTPException(
            status_code=503,
            detail=(
                "The demo is busy right now. "
                "Please try again in a few minutes."
            )
        )

    except Exception:
        traceback.print_exc()

        raise HTTPException(
            status_code=503,
            detail=(
                "Could not start a session. "
                "Please try again."
            )
        )

    # 4. Prevent overlapping turns
    if session.lock.locked():
        raise HTTPException(
            status_code=409,
            detail="A reply is still in progress."
        )

    # 5. Enforce demo turn cap
    if (
        settings.demo_mode
        and session.turns >= settings.max_turns_per_session
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "Demo limit reached for this session. "
                "Please refresh to start a new one."
            )
        )

    session.turns += 1

    # 6. Create event queue and statistics
    queue = asyncio.Queue()

    stats = {
        "ttft_ms": None,
        "tool_calls": 0,
        "outcome": "ok"
    }

    async def emit(event, data):

        if stats["ttft_ms"] is None:
            stats["ttft_ms"] = round(
                (time.perf_counter() - started) * 1000
            )

        if event == "tool_call":
            stats["tool_calls"] += 1

        if event == "guardrail":
            stats["outcome"] = f"guardrail_{data['kind']}"

        await queue.put((event, data))

    # 7. Create approval callback
    ask_approval = make_ask_approval(
        session.session_id,
        emit,
        pending,
        APPROVAL_TIMEOUT
    )

    # 8. Run agent in background
    async def run_and_close():
        async with session.lock:
            try:
                answer = await asyncio.wait_for(
                    run_turn(
                        session.agent,
                        session.chat,
                        req.message,
                        ask_approval,
                        max_turns=settings.max_turns,
                        emit=emit
                    ),
                    timeout=settings.turn_timeout_seconds
                )

                await emit(
                    "final",
                    {"text": answer}
                )

            except Exception as exc:
                traceback.print_exc()

                if isinstance(
                    exc,
                    (asyncio.TimeoutError, openai.APITimeoutError)
                ):
                    stats["outcome"] = "timeout"
                else:
                    stats["outcome"] = "error"

                await emit(
                    "error",
                    {"message": friendly_error(exc)}
                )

            finally:
                session.last_used = time.time()

                duration_ms = round(
                    (time.perf_counter() - started) * 1000
                )

                record = {
                    "duration_ms": duration_ms,
                    "ttft_ms": stats["ttft_ms"],
                    "outcome": stats["outcome"],
                    "tool_calls": stats["tool_calls"],
                    "session": session.session_id[:8]
                }

                metrics.append(record)
                log_json("turn", **record)

                await queue.put(None)

    # 9. Start task and retain reference
    task = asyncio.create_task(run_and_close())

    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    # 10. Stream events to browser
    async def event_stream():

        yield sse(
            "session",
            {"session_id": session.session_id}
        )

        while True:
            item = await queue.get()

            if item is None:
                break

            name, data = item

            yield sse(name, data)

    # 11. Return SSE response
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
