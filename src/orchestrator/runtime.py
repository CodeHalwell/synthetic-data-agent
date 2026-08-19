"""Helpers for running ADK agents programmatically from workflow code.

ADK agents are normally driven by a Runner (e.g. via ``adk web``). Workflows
that need a one-shot "prompt in, text out" call should use :func:`run_agent`,
which wraps the agent in a cached in-memory runner and executes the prompt in
a fresh session per call.
"""

from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

_WORKFLOW_USER_ID = "workflow"

# One runner per agent instance; sessions are created per call so invocations
# stay independent of each other.
_runners: dict[int, InMemoryRunner] = {}


def _get_runner(agent: BaseAgent) -> InMemoryRunner:
    key = id(agent)
    if key not in _runners:
        _runners[key] = InMemoryRunner(agent=agent, app_name=f"{agent.name}_workflow")
    return _runners[key]


async def run_agent(agent: BaseAgent, prompt: str) -> str:
    """Run an agent on a single prompt and return its final text response."""
    runner = _get_runner(agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id=_WORKFLOW_USER_ID
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_text = ""
    async for event in runner.run_async(
        user_id=_WORKFLOW_USER_ID, session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(part.text or "" for part in event.content.parts)
    return final_text
