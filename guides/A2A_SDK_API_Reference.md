# A2A SDK API Reference (Curated)

[`a2a_sdk_api_documentation.csv`](./a2a_sdk_api_documentation.csv) enumerates every class, method, enum, and helper exported by the SDK. This guide distills that catalogue into digestible sections so you can look up the right module quickly, then dive back into the CSV or source for details.

## Using the CSV Effectively

1. Open the file in a spreadsheet or query tool (it is comma-separated with headers).
2. Filter by `Category` (Core Classes, Request/Response, Events, Enumerations, etc.).
3. Use `Module` to locate the exact import path.
4. Reference this guide for high-level context, then consult the CSV for full method signatures and descriptions.

## Types (`a2a.types`)

| Category | Representative Symbols | Notes |
| --- | --- | --- |
| Core | `AgentCard`, `AgentSkill`, `AgentCapabilities`, `AgentSecurityScheme`, `SkillTag` | Define agent manifests and capability metadata. Keep AgentCards versioned and aligned with docs. |
| Tasks | `Task`, `TaskState`, `TaskStatus`, `TaskSummary`, `TaskListRequest`, `TaskListResponse` | Model lifecycle of work items. Task stores persist these objects. |
| Messages | `Message`, `MessageRole`, `MessagePart` variants (`TextPart`, `DataPart`, `FilePart`, `JsonPart`, `ToolResultPart`) | Structure chat transcripts; hosts rely on consistent roles and part types. |
| Artifacts | `Artifact`, `TextArtifact`, `JsonArtifact`, `FileArtifact` | Convey structured or binary outputs. Attach metadata (filename, MIME type) for host rendering. |
| Events | `TaskSubmittedEvent`, `TaskWorkingEvent`, `TaskCompletedEvent`, `TaskFailedEvent`, `TaskCanceledEvent`, `TaskStreamEvent` | Streamed over transports; hosts build timelines out of them. |
| Errors | `TaskNotFoundError`, `TaskNotCancelableError`, `UnsupportedOperationError`, `UnauthorizedError`, `ValidationError` | Standard error classes referenced by both server and client modules. |

## Server Package (`a2a.server`)

- **Applications** – `A2AStarletteApplication`, `A2AFastAPIApplication` wrap your executor and task store into ASGI apps. Choose the variant that matches your framework preferences.
- **Agent Execution** – `AgentExecutor`, `RequestContext`, `ContextMetadata`, `AgentExecutionError` manage task execution. Override `execute`/`cancel` and use context helpers (`get_user_input`, `get_metadata`, etc.).
- **Events** – `EventQueue`, `StreamingEventQueue`, `QueueFactory` coordinate event dispatch. Support progressive updates and batching.
- **Request Handlers** – `DefaultRequestHandler`, `StreamingRequestHandler`, `WebhookRequestHandler` orchestrate transports, security checks, and concurrency. Use `DefaultRequestHandler` unless you need custom webhook semantics.
- **Tasks** – `TaskStore` interface with implementations (`InMemoryTaskStore`, `RedisTaskStore`, `FirestoreTaskStore`, `SqlTaskStore`). Extend for bespoke persistence.
- **Extensions** – Middleware interfaces under `a2a.server.extensions`. Samples demonstrate timestamp and traceability injectors.

## Client Package (`a2a.client`)

- **Client Interfaces** – `Client`, `BaseClient`, `ClientFactory`, `ClientRegistry`. Factories allow registering custom transport/client combos.
- **Transports** – `RestTransport`, `JsonRpcTransport`, `GrpcTransport`, plus transport helpers. Determine which to use based on agent support: REST for synchronous interactions, JSON-RPC/WebSocket for streaming, gRPC for high-throughput.
- **Authentication** – `AuthInterceptor`, `CredentialProvider`, `APIKeyCredentials`, `OAuthCredentials`. Inject tokens per request or build interceptors for advanced schemes.
- **Task Management** – `ClientTaskManager`, `TaskPoller`, `EventConsumer` help hosts merge remote task events into local views (see `samples/python/hosts/multiagent`).
- **Errors** – `A2AClientError` hierarchy identifies protocol, HTTP, timeout, and validation failures. Use for retries and graceful degradation.

## Utilities (`a2a.utils`)

Key helpers used across samples:
- Message factories: `new_agent_text_message`, `new_agent_error_message`, `new_agent_progress_message`.
- Artifact creators: `new_text_artifact`, `new_json_artifact`, `save_file_artifact`.
- Task helpers: `new_task`, `clone_task_with_status`.
- Parsing utilities: `parse_agent_card`, `merge_agent_cards`.

Rely on these instead of crafting raw dictionaries—the SDK maintains compatibility as the spec evolves.

## Enumerations

Found across `a2a.enums` and type modules, including:
- `TaskState`, `TaskErrorCode`, `TaskSort`, `TransportProtocol`.
- `MessageRole`, `PartType`, `CapabilityFlag`.
- `AuthScheme`, `ToolInputType`, `ExtensionScope`.

Use enum values exactly as defined to avoid validation failures when interacting with other agents or the Inspector.

## Error Classes & Exceptions

- Client-side: `A2AClientError`, `A2AClientHTTPError`, `A2AClientJSONError`, `A2AClientTimeoutError`.
- Server-side: `AgentExecutionError`, `UnsupportedOperationError`, `UnauthorizedError`.

Wrap custom exceptions with these base classes so hosts receive consistent error codes and messages.

## Linking Docs & Samples

- Search `a2a-samples` for class names from the CSV to see real-world usage (e.g., `TaskStore` implementations, `ClientTaskManager`).
- Inspector uses `a2a.client` under the hood; reading its code helps understand transport negotiation.
- When the SDK updates, diff the CSV between versions to spot new modules or breaking changes, then update guides accordingly.

The CSV + this curated map give you a fast feedback loop: identify the symbol you need, confirm its signature, locate sample usage, and implement confidently.
