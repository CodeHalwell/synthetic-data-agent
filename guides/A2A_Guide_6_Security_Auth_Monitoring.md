# A2A Guide 6 · Security, Authentication & Monitoring

Agents frequently exchange untrusted data and can trigger downstream actions. This guide aggregates the security warnings scattered throughout `a2a-samples`, Inspector docs, and SDK behaviour, translating them into actionable controls for production deployments.

## 1. Threat Model

| Threat | Description | Mitigation |
| --- | --- | --- |
| Prompt Injection | Malicious AgentCards, messages, or artifacts attempt to hijack prompts. | Sanitize strings, apply allowlists for Markdown/HTML, isolate user-generated content, apply LLM content filters. |
| Data Exfiltration | Remote agents request or leak sensitive data. | Enforce data classification, redact logs, restrict tools/skills exposed to external agents. |
| Credential Theft | API keys or OAuth tokens leaked in repo or logs. | Store in secret managers, rotate regularly, never embed in samples. |
| Denial of Service | Agents stream excessive events or large artifacts. | Rate limit per agent, enforce payload size caps, implement back-pressure in hosts. |
| Protocol Abuse | Non-compliant AgentCards or messages crash hosts. | Validate against schema (Inspector), reject malformed payloads. |

## 2. Authentication & Authorization

1. **Transport Security** – Always serve agents over HTTPS. Use mutual TLS or ingress gateways for internal traffic.
2. **Security Schemes in AgentCards** – Populate the `security` block with scheme names (`api_key`, `oauth2`, `bearer`). Include `description` and `in` fields so hosts know how to supply credentials. Example from Auth-enabled samples:
   ```json
   "security": [{
     "scheme": "api_key",
     "in": "header",
     "name": "X-API-Key",
     "description": "Generated per host"
   }]
   ```
3. **Credential Rotation** – Adopt short-lived tokens. `a2a-samples/samples/python/agents/headless_agent_auth` demonstrates verifying API keys per request.
4. **Scoped Access** – Limit remote agent skills based on host role. For multi-tenant hosts, map host credentials to the skills they can invoke.

## 3. Sanitization & Validation

- Treat every AgentCard field as untrusted. Normalize whitespace, strip HTML, and reject oversized descriptions before using them in prompts.
- Validate tool schemas: enforce allowed types, maximum depth, and semantic checks (e.g., numeric ranges).
- When rendering artifacts, enforce MIME type allowlists and file size limits. Consider virus scanning for file uploads.
- Use JSON schema validation against incoming messages and metadata blocks to prevent injection attacks.

## 4. Network & Resource Controls

- Configure connection pools with sensible limits; throttle concurrent tasks per host/agent.
- Apply rate limiting per remote agent (requests/second, tasks/minute). The CLI host sample shows how to queue tasks; extend it with token buckets or leaky buckets.
- Enforce global timeout budgets; combine per-stage timeouts in your executor with overall task deadlines enforced by hosts.
- Use circuit breakers to disable misbehaving agents automatically when they breach error thresholds.

## 5. Monitoring & Telemetry

- **Metrics** – Capture request counts, latency, error rates, and payload sizes. Expose via Prometheus, Stackdriver, or your platform equivalent.
- **Structured Logging** – Log JSON objects containing `task_id`, `remote_agent`, `user_id` (hashed), correlation IDs, decision rationale. Avoid storing raw prompts unless redacted.
- **Traceability Extension** – Implement `extensions/traceability` to propagate trace metadata across agent boundaries. Hosts can then correlate entire conversations.
- **Inspector Automation** – Run the Inspector backend in CI to validate AgentCards and sample tasks, preventing regressions from merging insecure changes.
- **Alerting** – Configure alerts for spikes in `TaskFailedEvent` with security-related errors, unauthorized access attempts, or anomalies in task volume.

## 6. Incident Response Playbook

1. **Contain** – Revoke affected credentials, disable impacted agents via registry flags, and update AgentCards to reflect new security requirements.
2. **Investigate** – Use logs and traceability data to identify affected tasks and users. Export sanitized transcripts for forensic analysis.
3. **Communicate** – Notify stakeholders, partners, and compliance teams. Provide recommended mitigation steps for host operators.
4. **Remediate** – Patch vulnerabilities, update prompts, strengthen validation, and roll out new credentials.
5. **Review** – Post-incident review focusing on detection gaps, automation opportunities, and documentation updates.

## 7. Compliance Considerations

- Align data retention with regulatory obligations (GDPR, HIPAA, etc.). Implement deletion policies for task transcripts and artifacts.
- Document subprocessors and third-party services (LLM providers, MCP servers). Include them in privacy notices.
- For high-risk actions (financial transactions, infrastructure changes), implement human-in-the-loop approvals. See `a2a-samples/samples/python/agents/any_agent_adversarial_multiagent` for adversarial testing ideas.

## 8. Security Checklist

- [ ] AgentCard security schemes complete and documented.
- [ ] Secrets stored in vault/secret manager; `.env` files ignored by version control.
- [ ] Input validation with explicit allowlists for prompts, metadata, and tool payloads.
- [ ] Rate limiting and timeouts configured per agent.
- [ ] Telemetry pipeline capturing metrics, logs, and traces.
- [ ] Automated Inspector checks in CI/CD.
- [ ] Incident response runbook accessible and rehearsed.

Security is not an afterthought—design your agent ecosystem assuming peers can be malicious, monitor aggressively, and rehearse recovery scenarios before they happen.
