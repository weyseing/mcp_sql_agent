import os
import asyncio
import anthropic
from openai import OpenAI
from typing import Union, cast
from dotenv import load_dotenv
from dataclasses import dataclass, field
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from anthropic.types import MessageParam, TextBlock, ToolUnionParam, ToolUseBlock

# env
load_dotenv()

# OAI
openai_key = os.environ["OPENAI_API_KEY"]
oai_client = OpenAI(api_key=openai_key)

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["./mcp_server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)

@dataclass
class Chat:
    messages: list[MessageParam] = field(default_factory=list)

    system_prompt: str = """You are a master SQLite assistant. 
    Your job is to use the tools at your dispoal to execute SQL queries and provide the results to the user."""

    async def process_query(self, session: ClientSession, query: str) -> None:
        response = await session.list_tools()
        available_tools: list[ToolUnionParam] = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

        # Initial Claude API call
        res = await oai_client.messages.create(
            model="claude-3-5-sonnet-latest",
            system=self.system_prompt,
            max_tokens=8000,
            messages=self.messages,
            tools=available_tools,
        )

        assistant_message_content: list[Union[ToolUseBlock, TextBlock]] = []
        for content in res.content:
            if content.type == "text":
                assistant_message_content.append(content)
                print(content.text)
            elif content.type == "tool_use":
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await session.call_tool(tool_name, cast(dict, tool_args))

                assistant_message_content.append(content)
                self.messages.append(
                    {"role": "assistant", "content": assistant_message_content}
                )
                self.messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": getattr(result.content[0], "text", ""),
                            }
                        ],
                    }
                )
                # Get next response from Claude
                res = await anthropic_client.messages.create(
                    model="claude-3-7-sonnet-latest",
                    max_tokens=8000,
                    messages=self.messages,
                    tools=available_tools,
                )
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": getattr(res.content[0], "text", ""),
                    }
                )
                print(getattr(res.content[0], "text", ""))

    async def chat_loop(self, session: ClientSession):
        while True:
            query = input("\nQuery: ").strip()
            self.messages.append(
                MessageParam(
                    role="user",
                    content=query,
                )
            )

            await self.process_query(session, query)

    async def run(self):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()

                await self.chat_loop(session)


chat = Chat()

asyncio.run(chat.run())