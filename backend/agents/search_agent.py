from models.agents import SearchAgent
from models.skills import SearchSkill
from models.llm import LLMConfig
from a2a.types import AgentExecutor, RequestContext, EventQueue, new_agent_progress_message, new_agent_error_message
from a2a.utils import new_agent_text_message, new_json_artifact

class SearchAgentExecutor(SearchAgent, AgentExecutor):
    llm_config: LLMConfig = LLMConfig()
    search_skill: SearchSkill = SearchSkill()

    def __init__(self):
        super().__init__()
        self.version = "1.0.0"
        self.url = "https://search.agent.com"
        self.capabilities = ["search"]
        self.skills = [self.search_skill]

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        raw = context.get_user_input() or "{}"
        await event_queue.enqueue_event(new_agent_progress_message("Validating request", 5))
        try:
            request = self.search_skill.model_validate_json(raw)
        except Exception as exc:  # noqa: BLE001
            await event_queue.enqueue_event(new_agent_error_message(f"Validation error: {exc}"))
            return

        await event_queue.enqueue_event(new_agent_progress_message("Searching", 30))
        try:
            result = await self.search_skill.execute(request)
        except Exception as exc:  # noqa: BLE001
            await event_queue.enqueue_event(new_agent_error_message(f"Search failed: {exc}"))
            return False

        await event_queue.enqueue_event(new_agent_progress_message("Formatting response", 70))
        artifact = new_json_artifact(result)
        await event_queue.enqueue_event(new_agent_text_message(result.result))
        await event_queue.enqueue_event(artifact)
        return True

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        self.search_skill.cancel(context.get_task_id())
        await event_queue.enqueue_event(new_agent_text_message("Cancellation acknowledged."))