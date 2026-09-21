import asyncio
from fastmcp import Client
import os
import pathlib
from groq import Groq
from dotenv import load_dotenv
import json
import csv 
import datetime

load_dotenv()


project_root = os.path.dirname(os.path.abspath(__file__))
parent_root = os.path.dirname(project_root)
server_path = os.path.join(parent_root, "server", "pipeline_server.py")

client = Client(pathlib.Path(server_path))

async def main():
    async with client:
        tools = await client.list_tools()
        tool_schemas = build_tool_schemas(tools)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        while True:
                goal = input("\nYou: ")
                if goal.lower() in ("quit", "exit"):
                    break
            
                if goal.strip() == "/weekly_review":
                    prompt_result = await client.get_prompt("weekly_review")
                    goal = prompt_result.messages[0].content.text
            
                answer = await run_agent(goal, tool_schemas, messages)
                print(f"\nAgent: {answer}")

groq_client = Groq(api_key = os.environ.get("GROQ_API_KEY"))

def build_tool_schemas(mcp_tools):
    schemas = []
    for tool in mcp_tools:
        schemas.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            }
        })
    return schemas

SYSTEM_PROMPT = """
You are my job search assistant. You help me analyze and track job applications using my applications database. I record the companies I apply to each day, and I may ask for a quick summary of each application's current status and any follow-up actions or messages needed.
Always call `get_application` to retrieve the latest full application details before drafting any follow-up message. Never draft a follow-up based on vague memory or prior conversation context alone.
Treat `get_stale_applications` as the source of truth for determining which applications currently need action. Do not independently guess or infer whether an application is stale.
If `get_application` returns an ambiguous or suggested match, such as "did you mean Databricks?", do not treat that suggestion as confirmed. Do not repeatedly call the tool with the same unresolved name. Ask me to confirm the intended application unless the correct match can be established unambiguously from tool data.
Use tool data exactly as returned. Never invent or assume a company name, application stage, status, date, follow-up requirement, or other application detail that was not returned by a tool.
Before calling log_application or update_application, check whether the company already has an application on record. If the user's message about that company could mean either thing — logging a distinct new application (e.g., a different role at the same company) or updating the existing one (e.g., correcting a role title, changing stage) — do not choose automatically. Ask directly, for example: "Is this a new application for a different role at [company], or would you like to update your existing [company] application?" Only call log_application or update_application once that's clarified.
If required information is missing or uncertain, call the appropriate tool again when doing so can retrieve the missing information. If the tools still do not establish the answer, clearly say that the information is unavailable rather than guessing.
Stop calling tools once every part of my request has been answered using real tool data. Make no unnecessary or duplicate tool calls.
Return:
1. A concise plain-English summary first.
2. Specific application details and follow-up actions afterward.
   """

TOKEN_WARNING_THRESHOLD = 6000

def get_llm_response(messages, tool_schemas):
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=tool_schemas,
        tool_choice="auto",
    )

    used_tokens = response.usage.prompt_tokens
    if used_tokens >= TOKEN_WARNING_THRESHOLD:
        print("USED 75% OF TOKEN LIMIT PER SESSION")

    return response.choices[0].message

async def execute_tool_call(tool_call):

    arguments = json.loads(tool_call.function.arguments)
    result = await client.call_tool(tool_call.function.name, arguments)
    result_text = result.content[0].text

    return {
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": result_text,
}

MAX_STEPS = 5

async def run_agent(goal, tool_schemas, messages):

    messages.append({"role": "user", "content": goal})

    tool_calls_made = []

    for step in range(MAX_STEPS):
        message = get_llm_response(messages, tool_schemas)
        messages.append(message)

        if not message.tool_calls:
            log_run(goal, tool_calls_made, message.content)
            return message.content

        for tool_call in message.tool_calls:
            tool_calls_made.append(tool_call.function.name)
            if tool_call.function.name == "mark_followed_up":
                arguments = json.loads(tool_call.function.arguments)
                print(f"\nDraft follow-up for {arguments['company']}:\n{arguments['draft_text']}\n")
                approval = input("Send this follow-up? (y/n): ")

                if approval.lower() != "y":
                    messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": "The user did not approve this follow-up. It was not sent.",
                                })
                    continue
        

            tool_result = await execute_tool_call(tool_call)
            messages.append(tool_result)

    final_answer = "I wasn't able to complete this within the allowed number of steps."
    log_run(goal, tool_calls_made, final_answer)
    return final_answer

def log_run(goal, tool_calls_made, final_answer):

    logs_dir = os.path.join(parent_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "agent_runs.csv")

    file_exists = os.path.isfile(log_path)

    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "goal", "tool_calls", "final_answer"])
        writer.writerow([
            datetime.datetime.now().isoformat(),
            goal,
            "; ".join(tool_calls_made),
            final_answer,
        ])




if __name__ == "__main__":
    asyncio.run(main())

