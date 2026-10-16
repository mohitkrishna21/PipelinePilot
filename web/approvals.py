
import asyncio
import json


def make_ask_approval(session_id, emit, pending, timeout):

    async def ask_approval(name, arguments) -> bool:
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        pending[session_id] = future

        try:
            parsed = json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            parsed = arguments

        try:
            await emit(
                "approval_required",
                {
                    "tool": name,
                    "arguments": parsed
                }
            )

            ok = await asyncio.wait_for(
                future,
                timeout=timeout
            )

        except asyncio.TimeoutError:
            ok = False

        finally:
            pending.pop(session_id, None)

        return ok

    return ask_approval


def resolve_approval(session_id, decision, pending) -> bool:
    future = pending.get(session_id)

    if future is None or future.done():
        return False

    future.set_result(decision)

    return True
