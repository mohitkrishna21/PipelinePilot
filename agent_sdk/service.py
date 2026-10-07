from agents import Agent, Runner, SQLiteSession
from agents.exceptions import MaxTurnsExceeded

MAX_TURNS = 8

#Runner.run accepts only the agent and the input positionally. Options like max_turns and session must be keyword arguments, so write session=session
async def run_turn(agent: Agent, session: SQLiteSession, user_text:str)-> str:

    try:
        result = await Runner.run(agent, user_text, session=session, max_turns=MAX_TURNS)
    except MaxTurnsExceeded :
        return"I hit my step limit before finishing, try a narrower question."

    return result.final_output