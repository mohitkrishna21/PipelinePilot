import asyncio,os
from dotenv import load_dotenv
from agents import SQLiteSession
from agents.mcp import MCPServerStdio
from agent_sdk.agents import build_pipeline_assistant
from agent_sdk.service import run_turn

async def cli_approval(tool_name: str, arguments: str) -> bool:
    print(f"\nApproval needed: {tool_name}")
    print(arguments)

    answer = input("Approve? (y/n): ")
    return answer.strip().lower() == "y"

async def main()->None:

    load_dotenv()
    server_python = os.environ["SERVER_PYTHON"]

    params= {"command":server_python, "args":["server/pipeline_server.py"]}

    async with MCPServerStdio(name="pipeline", params=params, cache_tools_list=True, require_approval={"always":{"tool_names":["mark_followed_up"]}}) as server:
        agent = build_pipeline_assistant(server)
        session = SQLiteSession("pipeline-cli", "sdk_sessions.db")

        while True:
            user_text = input("You: ").strip()

            if user_text == "":
                continue
            if user_text.lower() in ("exit","quit"):
                break


            answer = await run_turn(agent, session, user_text, cli_approval)
            print("Assistant: "+answer)

if __name__ == "__main__":
    asyncio.run(main())


