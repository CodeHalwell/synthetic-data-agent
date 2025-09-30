# A2A Guide 4 · Framework Integration

Connect your preferred agent frameworks, orchestration libraries, and platform SDKs to A2A without rewriting business logic. This guide catalogues proven integration patterns from `a2a-samples` across Python, JavaScript, Java, .NET, and Go.

## 1. Integration Strategy

1. **Wrap Instead of Rebuild** – Keep your existing framework pipelines intact. The `AgentExecutor` should only translate between `RequestContext`/`EventQueue` and the framework’s input/output structures.
2. **Normalize Input Contracts** – Validate incoming tasks and convert them into the framework’s expected schema before invoking the workflow. Return clear validation errors rather than letting frameworks throw unhandled exceptions.
3. **Stream Meaningful Events** – Map framework callbacks (thoughts, tool calls, partial responses) to A2A events (`new_agent_progress_message`, `new_agent_text_message`, artifacts). Hosts benefit from visibility into intermediate steps.
4. **Centralize Configuration** – Pull model/provider configuration from `config/congfig.py` or a dedicated config module so you can swap providers without touching the executor.

## 2. Python Ecosystem

| Framework | How to Adapt | Sample Highlights |
| --- | --- | --- |
| **LangChain** | Create the chain/agent separately, wire callbacks that push token streams or tool logs into `EventQueue`. Use `ChatPromptTemplate` stored under `models/`. | `samples/python/agents/helloworld`, `agents/analytics` |
| **LangGraph** | Manage graph state in a class; call `app.astream_events()` within `execute()` and forward each event to A2A. Track per-task state to support retries. | `samples/python/agents/langgraph` |
| **CrewAI** | Instantiate crew tasks with environment-configured models. Emit progress updates before/after `crew.kickoff()` to avoid perceived timeouts. | `samples/python/agents/crewai` |
| **LlamaIndex** | Turn uploaded files into `Document` objects, maintain a vector store, and map streaming responses to A2A text messages. | `samples/python/agents/llama_index_file_chat` |
| **Marvin / MindsDB / AG2** | Wrap each framework’s run function, ensuring attachments and tool outputs conform to A2A message parts. | `samples/python/agents/marvin`, `mindsdb`, `ag2` |
| **Google ADK** | Use ADK’s tool infrastructure but surface them via `AgentCard.tools`. Executors mostly perform translation between ADK events and A2A events. | `samples/python/agents/adk_*` |
| **Azure AI Foundry** | Mirror auth flow (`AZURE_*` env vars) and convert Foundry responses into A2A events. | `samples/python/agents/azureaifoundry_sdk` |

### Example: LangGraph Executor Adapter
```python
class LangGraphExecutor(AgentExecutor):
    def __init__(self, graph_app):
        self._app = graph_app

    async def execute(self, context, event_queue):
        state = {"input": context.get_user_input(), "task_id": context.get_task_id()}
        async for event in self._app.astream_events(state):
            if event.type == "node_started":
                await event_queue.enqueue_event(new_agent_progress_message(f"⏳ {event.node}"))
            elif event.type == "token":
                await event_queue.enqueue_event(new_agent_text_message(event.token, append=True))
            elif event.type == "completed":
                await event_queue.enqueue_event(new_agent_text_message(event.result))
```

## 3. JavaScript / TypeScript

- **Node Agents** (`samples/js/src/agents`) use the JS SDK to expose skills. Adopt ESM modules, use `dotenv` for configuration, and stream events over WebSocket or SSE.
- **Front-end Hosts**: Pair with frameworks like Next.js or Vercel AI SDK. Ensure CORS and authentication align with the AgentCard’s security schemes.
- **Tooling**: Use TypeScript interfaces mirroring the AgentCard schema to guarantee manifest accuracy.

## 4. Java

- **Spring Boot Implementation** (`samples/java/custom_java_impl`) shows wiring of controllers to expose JSON-RPC and REST endpoints. Use `AgentCardBuilder` to avoid manual JSON.
- **MCP Bridge**: Java Weather MCP agent demonstrates converting MCP tool schemas to A2A. Pay attention to Jackson annotations for serialization.
- **Testing**: Rely on `MockMvc` and integration tests to validate Task endpoints. Use `Testcontainers` when verifying persistence backends.

## 5. .NET

- Utilize the .NET SDK to integrate Semantic Kernel or custom orchestrators (`samples/dotnet/A2ASemanticKernelDemo`).
- Implement async streams for progress updates (`IAsyncEnumerable<A2AEvent>`). Make sure to flush output on each update to avoid buffering delays.
- For console hosts (CLI demo), parse arguments into Task payloads and handle cancellation tokens gracefully.

## 6. Go

- The Go SDK supports both server and client components (`samples/go/server`, `samples/go/client`).
- Leverage Go routines for parallel workflows but guard shared state with mutexes or channels.
- Use context deadlines for external calls; propagate cancellation through `context.Context`.

## 7. Cross-Cutting Concerns

- **Serialization** – Verify tool parameters and messages are JSON-serializable. Use enumerations defined in the SDK rather than ad-hoc strings.
- **Attachments** – Convert framework-specific file representations into A2A artifacts. For large binaries, upload to storage and return signed URLs (the Mesop demo hints at this pattern).
- **Error Mapping** – Each framework raises its own exceptions; translate them into `new_agent_error_message` payloads with actionable advice. Categorize using `TaskErrorCode` where applicable.
- **Telemetry** – Inject middleware (see Guide 7) to add tracing, logging, and metrics around framework calls. For example, wrap LangChain run in an OpenTelemetry span.

## 8. Verification Checklist

- [ ] AgentCard accurately describes framework-specific capabilities and required configuration.
- [ ] Framework callbacks tested to ensure streaming output arrives in order (use Inspector for manual verification).
- [ ] Dependency versions documented; align with the ones in `a2a-samples` to avoid incompatibilities.
- [ ] Credentials loaded from environment or secret manager, never hard-coded.
- [ ] Release notes include framework-specific caveats (rate limits, payload size limits, supported content types).

Following these patterns lets you combine the ecosystem’s best tooling with the A2A contract, ensuring hosts can consume your agent regardless of underlying framework or language choice.
