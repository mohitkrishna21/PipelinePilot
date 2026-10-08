from agents import Agent, Runner, SQLiteSession
from agents.exceptions import MaxTurnsExceeded

MAX_TURNS = 8

#Runner.run accepts only the agent and the input positionally. Options like max_turns and session must be keyword arguments, so write session=session
async def run_turn(agent: Agent, session: SQLiteSession, user_text:str, ask_approval)-> str:

    try:
        result = await Runner.run(agent, user_text, session=session, max_turns=MAX_TURNS)
        while result.interruptions:
            state = result.to_state()

            for item in result.interruptions:
                ok = await ask_approval(item.name, item.arguments)

                if ok:
                    state.approve(item)
                else:
                    state.reject(item)
            result = await Runner.run(agent,state,session=session,max_turns=MAX_TURNS)  
                 
    except MaxTurnsExceeded :
        return"I hit my step limit before finishing, try a narrower question."

    return result.final_output