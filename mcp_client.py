import sys
import logging
import asyncio
import anthropic
from loguru import logger
from typing import Union, cast
from dotenv import load_dotenv
from dataclasses import dataclass, field
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from anthropic.types import MessageParam, TextBlock, ToolUnionParam, ToolUseBlock

# env
load_dotenv()

# logging
logging.basicConfig(
    stream=sys.stderr,
    format="\033[94m%(asctime)s\033[0m - \033[92m%(levelname)s\033[0m - \033[93m%(filename)s:%(lineno)d\033[0m: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

# LLM client
anthropic_client = anthropic.AsyncAnthropic()

# stdio server
server_params = StdioServerParameters(
    command="python",
    args=["./mcp_server.py"],
    env=None,
)

@dataclass
class Chat:
    # message & system msg
    messages: list[MessageParam] = field(default_factory=list)
    system_prompt: str = """You are a master SQLite assistant. 
    Your job is to use the tools at your dispoal to execute SQL queries and provide the results to the user."""

    async def process_query(self, session: ClientSession, query: str) -> None:\
        # get MCP tools
        response = await session.list_tools()
        available_tools: list[ToolUnionParam] = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]
        logging.info(f"Available MCP tools: {available_tools}")

        # get MCP prompts
        response = await session.list_prompts()
        logging.info(f"Available MCP prompts: {str(response)}")

        # call LLM
        res = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-latest",
            system=self.system_prompt,
            max_tokens=8000,
            messages=self.messages,
            tools=available_tools,
        )

        assistant_message_content: list[Union[ToolUseBlock, TextBlock]] = []
        for content in res.content:
            # text response
            if content.type == "text":
                assistant_message_content.append(content)
                logging.info(f"Response: {content.text}")
            # tool response
            elif content.type == "tool_use":
                tool_name = content.name
                tool_args = content.input
                logging.info(f"Tool: {str(content)}")

                # call tool
                result = await session.call_tool(tool_name, cast(dict, tool_args))

                # chat history
                assistant_message_content.append(content)
                self.messages.append({"role": "assistant", "content": assistant_message_content})
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
                logging.info(f"Chat history: {str(self.messages)}")

                # call LLM
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
                logging.info(f"Chat history: {str(self.messages)}")
                logging.info(f"Response: {getattr(res.content[0], "text", "")}")

    async def chat_loop(self, session: ClientSession):
        while True:
            query = input("\nQuery: ").strip()
            self.messages.append(MessageParam(role="user", content=query,))
            await self.process_query(session, query)

    async def run(self):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await self.chat_loop(session)

chat = Chat()
asyncio.run(chat.run())