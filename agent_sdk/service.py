from agents import Agent, Runner, SQLiteSession
from agents.exceptions import (
    MaxTurnsExceeded,
    OutputGuardrailTripwireTriggered,
    InputGuardrailTripwireTriggered,
)


MAX_TURNS = 8

OUTPUT_BLOCK_MSG = (
    "Blocked: that Pitch Note claimed experience that is not in your "
    "resume facts. I won't show a Pitch Note that overstates your background."
)

INPUT_BLOCK_MSG = "That request was blocked by the input safety check."


async def run_turn(
    agent: Agent,
    session: SQLiteSession,
    user_text: str,
    ask_approval,
    *,
    max_turns=MAX_TURNS,
    emit=None
) -> str:

    try:
        names = {}

        result = Runner.run_streamed(
            agent,
            user_text,
            session=session,
            max_turns=max_turns
        )

        await _forward_events(result, emit, names)

        while result.interruptions:
            state = result.to_state()

            for item in result.interruptions:
                ok = await ask_approval(item.name, item.arguments)

                if ok:
                    state.approve(item)
                else:
                    state.reject(item)

            result = Runner.run_streamed(
                agent,
                state,
                session=session,
                max_turns=max_turns
            )

            await _forward_events(result, emit, names)

    except MaxTurnsExceeded:
        return "I hit my step limit before finishing, try a narrower question."

    except OutputGuardrailTripwireTriggered:
        if emit is not None:
            await emit(
                "guardrail",
                {
                    "kind": "output",
                    "message": OUTPUT_BLOCK_MSG
                }
            )

        return OUTPUT_BLOCK_MSG

    except InputGuardrailTripwireTriggered:
        if emit is not None:
            await emit(
                "guardrail",
                {
                    "kind": "input",
                    "message": INPUT_BLOCK_MSG
                }
            )

        return INPUT_BLOCK_MSG

    return result.final_output

async def _forward_events(result, emit, names):
    async for event in result.stream_events():

        if event.type != "run_item_stream_event":
            continue

        if event.name == "tool_called":
            raw = event.item.raw_item

            names[raw.call_id] = raw.name

            if emit is not None:
                await emit(
                    "tool_call",
                    {
                        "name": raw.name,
                        "arguments": str(raw.arguments)[:300]
                    }
                )

        elif event.name == "tool_output":
            raw = event.item.raw_item
            call_id = raw["call_id"]

            tool = names.get(call_id, "unknown")
            output = event.item.output

            if emit is not None:
                await emit(
                    "tool_result",
                    {
                        "name": tool,
                        "output": str(output)[:2000]
                    }
                )

                if tool == "analyze_job_description":
                    if hasattr(output, "model_dump"):
                        data = output.model_dump()

                    elif isinstance(output, dict):
                        data = output

                    else:
                        data = None

                    if data is not None:
                        await emit(
                            "jd_breakdown",
                            data
                        )
