# A2A Guide 5 · MCP Integration

Model Context Protocol (MCP) exposes tool inventories over WebSockets or Server-Sent Events. Bridging MCP into A2A lets you reuse existing MCP tools while benefiting from the A2A task lifecycle, streaming events, and host interoperability. This guide expands on the MCP samples in `a2a-samples`:

- `samples/python/agents/a2a_mcp`
- `samples/python/agents/a2a-mcp-without-framework`
- `samples/java/agents/weather_mcp`
- `samples/python/agents/azureaifoundry_sdk/multi_agent/mcp_sse_server`

## 1. Bridge Architecture

```
┌─────────────┐   A2A Tasks/Events   ┌──────────────┐   MCP Requests   ┌─────────────┐
│   A2A Host  │ ───────────────────▶ │ MCP Bridge   │ ───────────────▶ │ MCP Server  │
│ (CLI / UI)  │ ◀─────────────────── │ (A2A Agent)  │ ◀─────────────── │   Tools      │
└─────────────┘                      └──────────────┘                  └─────────────┘
```

The bridge is just another A2A agent. It accepts tasks, translates them into MCP invocations, and forwards MCP responses back as A2A events.

## 2. Implementation Steps

1. **Model Tools in the AgentCard**
   - Pull tool metadata from the MCP server (`list_tools`), then convert each definition into an `AgentSkill` + `Tool` schema.
   - The Python sample includes `mcp_tool_to_agent_skill` utilities that translate JSON Schema into A2A-compatible parameter definitions.

2. **Establish MCP Session**
   - Use the official `mcp` Python or Java client to open a WebSocket/SSE connection.
   - Handle authentication tokens and session heartbeats; store them in a bridge-level service so they survive multiple tasks.

3. **Translate Requests**
   - Inside `AgentExecutor.execute()`, parse the incoming task payload (text or structured metadata).
   - Map to MCP operations (`call_tool`, `prompt`, `resource`) using the tool ID that matches the skill invoked.
   - Stream MCP responses: textual output → `new_agent_text_message`, JSON payloads → `new_json_artifact`, binary data → `new_file_artifact`.

4. **Error Handling & Recovery**
   - Retry transient MCP errors (network disconnects, 5xx) with exponential backoff.
   - Surface structured errors to hosts with actionable descriptions (e.g., “MCP tool unavailable, try again later”).
   - Provide specific `TaskErrorCode`s when possible so orchestrators can branch logic.

5. **Clean Shutdown**
   - Implement `cancel()` to forward cancellation to the MCP server and clean up sessions.
   - Close WebSocket connections on application shutdown to avoid orphaned sessions.

## 3. Python Bridge Walkthrough

```bash
cd a2a-samples/samples/python/agents/a2a_mcp
uv run . -- --mcp-url wss://your-mcp-endpoint --api-key $MCP_KEY
```

- The script fetches tool metadata at startup and logs converted AgentCard entries.
- Connect via Inspector to ensure the skills reflect MCP tools.
- Use `samples/python/hosts/cli` to send a request and verify that MCP responses stream back as A2A events.

For a framework-free version (useful for embedding in custom runtimes), explore the `a2a-mcp-without-framework` sample—this demonstrates manual construction of AgentCards, transports, and MCP request mapping.

## 4. Java Weather MCP Agent

```bash
cd a2a-samples/samples/java/agents/weather_mcp
./gradlew bootRun
```

- Spring Boot handles HTTP/JSON-RPC endpoints while the MCP client runs in a managed bean.
- AgentCard is generated via builder APIs; ensure `description`, `skills`, and `security` fields reflect MCP requirements.
- Integration tests use mocked MCP responses to validate translation logic—replicate this strategy for your own agents.

## 5. Azure AI Foundry MCP Host

The Azure sample demonstrates running an MCP server via Azure Functions and connecting through SSE.

```bash
cd a2a-samples/samples/python/agents/azureaifoundry_sdk/multi_agent/mcp_sse_server
uv run . -- --endpoint https://<function-app>.azurewebsites.net --api-key $AZURE_MCP_KEY
```

It showcases:
- Multi-agent orchestration where one remote agent proxies MCP tools hosted in Azure.
- Secure secrets management via environment variables and the AgentCard’s `security.schemes` block.

## 6. Best Practices

- **Credential Management** – Store MCP credentials in secret managers. Advertise schemes via AgentCard so hosts know whether to include API keys, OAuth tokens, or session cookies.
- **Schema Drift Detection** – Watch for MCP tool schema changes. Re-run tool discovery regularly and bump the AgentCard `version` when capabilities change.
- **Performance** – Cache MCP tool metadata; avoid re-fetching on every task. Pool connections if the server supports it.
- **Timeouts** – Set request deadlines to prevent hanging tasks. Provide fallback responses or suggestions when MCP services are degraded.
- **Observability** – Log MCP request IDs alongside A2A `task_id`. Traceability extensions (Guide 7) help correlate events across both protocols.

## 7. Testing & Validation

1. Unit-test the translation layer: feed synthetic MCP responses and assert emitted A2A events.
2. Use Inspector to confirm AgentCard validity and streaming behaviour.
3. If possible, run the MCP server’s own diagnostics alongside Inspector to compare request payloads.
4. Simulate failure scenarios (auth revoked, tool disabled) and verify the bridge surfaces clear remediation steps.

MCP bridges let you leverage rich tool ecosystems without forcing hosts to speak MCP directly. With accurate manifests, resilient session handling, and thorough validation, you can operate MCP-backed agents as first-class citizens in your A2A deployment.
