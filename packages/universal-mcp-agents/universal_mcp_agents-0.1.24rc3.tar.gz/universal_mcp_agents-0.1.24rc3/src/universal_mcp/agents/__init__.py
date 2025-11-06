from typing import Literal

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.bigtool import BigToolAgent
from universal_mcp.agents.builder.builder import BuilderAgent
from universal_mcp.agents.codeact0 import CodeActPlaybookAgent
from universal_mcp.agents.react import ReactAgent
from universal_mcp.agents.simple import SimpleAgent
from universal_mcp.agents.codeact00 import CodeActPlaybookAgent as CodeAct00Agent
from universal_mcp.agents.codeact01 import CodeActPlaybookAgent as CodeAct01Agent


def get_agent(
    agent_name: Literal["react", "simple", "builder", "bigtool", "codeact-repl", "codeact-00", "codeact-01"],
):
    print("agent_name", agent_name)
    if agent_name == "react":
        return ReactAgent
    elif agent_name == "simple":
        return SimpleAgent
    elif agent_name == "codeact-repl":
        return CodeActPlaybookAgent
    elif agent_name == "codeact-00":
        return CodeAct00Agent
    elif agent_name == "codeact-01":
        return CodeAct01Agent
    else:
        raise ValueError(f"Unknown agent: {agent_name}. Possible values:  react, simple, codeact-repl, codeact-00, codeact-01")


__all__ = [
    "BaseAgent",
    "ReactAgent",
    "SimpleAgent",
    "BuilderAgent",
    "BigToolAgent",
    "CodeActScript",
    "CodeActRepl",
    "CodeAct00Agent",
    "CodeAct01Agent",
]
