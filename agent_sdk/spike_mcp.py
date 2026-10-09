import asyncio
import os
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio

async def list_server_tools()->list[str]:

    load_dotenv()
    server_python = os.environ["SERVER_PYTHON"]
    params= {"command":server_python, "args":["server/pipeline_server.py"]}

    async with MCPServerStdio(name="pipeline", params=params, cache_tools_list=True) as server:
        tools = await server.list_tools()

        tool_names= []
        for tool in tools :
            name = tool.name
            tool_names.append(name)

        return tool_names

if __name__=="__main__":
    print(asyncio.run(list_server_tools()))