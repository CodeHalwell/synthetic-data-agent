# A2A Guide 3 · Multi-Agent Systems

Scale beyond a single executor by composing hosts, orchestrators, and remote agents. This guide unpacks the working examples in `a2a-samples`—notably `demo/ui`, `samples/python/hosts/*`, and `agents/airbnb_planner_multiagent`—and outlines production guardrails for coordinating fleets of agents.

## 1. Core Roles & Responsibilities

| Role | Description | Sample References |
| --- | --- | --- |
| **Host / Orchestrator** | Owns end-user channels, creates tasks against remote agents, aggregates results. | `samples/python/hosts/cli`, `hosts/multiagent/host_agent.py`, `demo/ui` Mesop app |
| **Remote Agent** | Self-contained A2A server exposing skills via its AgentCard. | `agents/adk_expense_reimbursement`, `agents/langgraph`, Java `content_writer` |
| **Bridge Agent** | Wraps alternative protocols (MCP, REST, Vertex AI) and presents them as A2A skills. | `agents/a2a_mcp`, Azure Foundry sample, Java MCP weather agent |
| **Task Store** | Shared persistence for task timelines across host and remote agents. | Redis/Firestore/SQL stores in Python + Go hosts |

## 2. Topologies

1. **Hub-and-Spoke (Fan-Out)** – A central host delegates tasks to multiple remote specialists and merges outcomes. Used by the Mesop demo: the host agent decides which remote agent to ping based on skill tags.
2. **Cascading (Planner + Workers)** – Planner agent invokes downstream workers sequentially. Example: `airbnb_planner_multiagent` where a planner agent consults weather and rental agents.
3. **Federated Hosts** – Multiple hosts share a registry and task store, enabling redundancy or geographic sharding. Implement by centralizing agent discovery in a datastore and running identical host instances behind a load balancer.

Choose topology based on latency, responsibility boundaries, and trust domains.

## 3. Discovery & Registry Management

- Maintain a registry (database, config service, or GitOps manifest) holding remote agent URLs, AgentCard hashes, and allowed skills.
- On start-up, fetch each AgentCard and validate via the Inspector backend. Cache manifests with TTL equal to the AgentCard’s `cache_ttl` (if provided) or a sensible default (e.g., 5 minutes).
- Watch for `version` bumps—treat them as signals to re-validate schema compatibility and refresh tooling.
- Provide a manual override to disable an agent quickly (toggle in DB or mark as quarantined); hosts should respect this flag before delegating.

## 4. Routing Logic

### Skill-Based Routing

1. Parse user intent via NLP, rules, or LLM classification.
2. Match to skill tags or tool IDs advertised by remote AgentCards.
3. Prioritize based on latency history, success rate, or policy (e.g., prefer internal agents for sensitive data).

Example: `samples/python/hosts/content_creation` maps requests containing “image”, “video”, or “documentation” to separate remote agents.

### Scoring & Arbitration

- Use weighted scores—e.g., `score = capability_match + freshness_bonus - latency_penalty`.
- Capture decision metadata in logs for later auditing.
- In complex orchestrations, involve human review (Guide 6 suggests human-in-the-loop gates for sensitive actions).

## 5. Task Lifecycle Across Agents

1. Host submits task to Remote A via `A2AClient.send_message()`.
2. Remote A streams events; host ingests them into its `ClientTaskManager` and optionally forwards them to the end user.
3. Host decides to call Remote B (e.g., conversion service) using the output of Remote A as input metadata.
4. Host aggregates final outputs (text, artifacts) and returns them to the end user.

Implementation tips:
- Propagate metadata: include `trace_id`, `user_id`, and `parent_task_id` in each `send_message()` call (custom metadata block) so downstream agents can log consistently.
- Handle artifacts carefully—normalize filenames, MIME types, and storage locations. The Mesop demo stores artifacts in-memory; production systems should persist them to durable storage and return signed URLs.
- Implement cancellation fan-out: when a user cancels, host iterates through all active remote `task_id`s and calls `cancel_task()`.

## 6. Running the Mesop Multi-Agent Demo Locally

```bash
# 1. Start remote agents
cd a2a-samples/samples/python/agents/adk_expense_reimbursement
uv run .

cd ../langgraph
uv run .

# 2. Start host UI
cd ../../../demo/ui
uv run main.py
```

Open http://127.0.0.1:12000, add remote agents via the robot icon (e.g., `http://localhost:10002`), and start a chat. Use the **History** tab to see cross-agent message flow and **Tasks** tab to inspect streaming events.

## 7. Cross-Language Considerations

- **JavaScript/TypeScript** – `samples/js/src/agents` illustrates Vercel/Next integrations. Ensure Node hosts maintain persistent WebSocket connections for streaming.
- **Java** – Custom implementation shows how to expose REST + JSON-RPC endpoints with Spring Boot. Use bean-scoped clients to manage resource usage.
- **Go** – High-throughput hosts using gRPC. Pay attention to context timeouts and connection pooling.
- **.NET** – Semantic Kernel sample demonstrates orchestrators with strong typing; ensure asynchronous streams are awaited properly to avoid dropped events.

Interoperability is guaranteed by the spec, but each language’s SDK may lag features—consult the CSV and release notes before relying on a module.

## 8. Security & Governance

- Vet AgentCards before onboarding—confirm security schemes, prompt injection safeguards, and compliance with your data policies.
- Run vulnerability scans on remote agent container images.
- Track SLAs per agent (p95 latency, error rate). Consider auto-suspending agents that exceed thresholds.
- If remote agents belong to partner organizations, formalize contracts covering allowed inputs/outputs, logging, and rotation cadence for credentials.

## 9. Monitoring & Troubleshooting

- Aggregate logs by `trace_id` so you can follow a conversation across host and remote services. The traceability extension provides a documentation-backed schema for this.
- Mirror Inspector functionality in production by capturing and redacting task transcripts. Use them to reproduce bugs in staging.
- Implement dashboards: one per remote agent showing requests/minute, active tasks, failure codes. Use data to right-size concurrency limits and implement adaptive throttling.

## 10. Production Readiness Checklist

- [ ] Agent registry with health indicators, version tracking, and a disable switch.
- [ ] Automated AgentCard validation (Inspector or schema validation) at deploy time.
- [ ] Resilient retry and timeout strategies per remote agent.
- [ ] Observability stack capturing task traces across host and agents.
- [ ] Documented escalation path when an agent misbehaves (support contacts, rollback procedures).
- [ ] Test suites covering orchestration logic (simulate remote agents with canned responses to validate routing decisions).

By following the patterns codified in `a2a-samples` and reinforcing them with monitoring and governance, you can orchestrate a network of agents that collaborate reliably across transports, frameworks, and organizations.
