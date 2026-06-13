"""
ReAct agent setup for document retrieval and question answering.
"""

import os

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from src.config.settings import Config
from src.llms.openai import llm
from src.rag.retriever_setup import get_retriever

config = Config()

_agent_executor = None


def get_agent_executor() -> AgentExecutor:
    """
    Get or create the cached ReAct AgentExecutor.
    """
    global _agent_executor

    if _agent_executor is None:
        # Initialize tools lazily
        tools = [get_retriever()]

        # Load document description if available
        if os.path.exists("description.txt"):
            try:
                with open("description.txt", "r", encoding="utf-8") as f:
                    description = f.read().strip()
            except Exception:
                description = None
        else:
            description = None

        # Create ReAct agent prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", config.prompt("system_prompt")),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])

        # Initialize the ReAct agent and executor
        react_agent = create_react_agent(llm, tools, prompt)
        _agent_executor = AgentExecutor(
            agent=react_agent,
            tools=tools,
            handle_parsing_errors=True,
            max_iterations=2,
            verbose=True,
            return_intermediate_steps=True
        )

    return _agent_executor


def reset_agent_executor() -> None:
    """
    Reset the cached AgentExecutor to force reconstruction (e.g. when new docs are uploaded).
    """
    global _agent_executor
    _agent_executor = None

