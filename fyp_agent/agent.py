from __future__ import annotations

from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.mcp import MCPServer

from .config import Settings


SYSTEM_PROMPT = """You are a CML network lab assistant for an academic FYP.

You help inspect Cisco Modeling Labs (CML) state through MCP tools. In this
phase you are read-only. Query existing CML state before answering operational
questions. Do not invent lab names, node names, interface names, command output,
or topology details.

You must not create, delete, wipe, configure, start, or stop labs or nodes. You
must not send CLI commands. If the user asks for a mutating action, explain that
this first-phase harness is restricted to safe read-only inspection and suggest
what read-only information can be collected instead.

When a CML tool fails, summarize the error faithfully and suggest the next
diagnostic step, such as checking credentials, VPN/CUHK network access, SSL
verification, CML availability, or whether the requested lab/node exists.
"""


def build_agent(settings: Settings, mcp_server: MCPServer) -> Agent:
    model = settings.model_name
    if settings.llm_provider == "deepseek":
        client = AsyncOpenAI(
            api_key=settings.provider_api_key,
            base_url=settings.provider_base_url,
        )
        model = OpenAIChatCompletionsModel(
            model=settings.model_name,
            openai_client=client,
            strict_feature_validation=False,
        )

    return Agent(
        name="FYP CML Read-Only Agent",
        instructions=SYSTEM_PROMPT,
        model=model,
        mcp_servers=[mcp_server],
        mcp_config={
            "convert_schemas_to_strict": True,
            "include_server_in_tool_names": False,
        },
    )
