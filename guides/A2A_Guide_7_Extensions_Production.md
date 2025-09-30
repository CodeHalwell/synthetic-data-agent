# A2A Guide 7 · Extensions & Production Operations

After your agents pass functional and security checks, focus on platform-wide capabilities: protocol extensions, deployment pipelines, observability, and operational excellence. This guide draws on the extension specs and production examples in `a2a-samples` and `a2a-inspector`.

## 1. Extension Fundamentals

- **Specification** – Each extension is defined by a contract (often Markdown + JSON schema) describing new events, headers, or payload fields. Examples: `extensions/timestamp/v1/spec.md`, `extensions/traceability/v1/spec.md`.
- **Activation** – Agents advertise supported extensions in the AgentCard (`extensions` array). Hosts use this to negotiate features.
- **Implementation** – Register middleware/hooks on the server and client side. In Python, wrap `DefaultRequestHandler` or `EventQueue` with interceptors.

### Example: Timestamp Extension
1. Review `spec.md` to understand required metadata.
2. Implement server interceptor (`samples/python/extensions/timestamp`) that stamps outgoing events.
3. Update AgentCard with:
   ```json
   "extensions": [{"id": "timestamp", "version": "1.0.0"}]
   ```
4. Update host/client to read the metadata and expose it in UI/logs.

## 2. Observability & Traceability

- Deploy the traceability extension to tag every event with correlation IDs, timestamps, and routing metadata. Hooks exist in Python and Go samples.
- Forward these events to a tracing backend (OpenTelemetry collectors, Cloud Trace). Use spans to visualise multi-agent flows end-to-end.
- Provide dashboards that slice metrics by agent, skill, and extension version.

## 3. Deployment Pipeline

1. **Build** – Use reproducible builds (`uv` for Python, `npm run build` for Inspector, container images via Docker/Podman). Follow `demo/ui/Containerfile` or `a2a-inspector/Dockerfile` as references for multi-stage builds.
2. **Package** – Tag images with semantic versions matching the AgentCard `version`. Store manifests alongside artifacts.
3. **Release** – Automate rollouts (Kubernetes, Cloud Run, App Engine). Include health checks (`/healthz`) and readiness probes verifying key dependencies (LLM provider, task store, extension services).
4. **Rollback** – Keep previous images and AgentCards ready. Hosts should cache the last known-good manifest to support fast downgrade.

## 4. Scaling Strategies

- **Horizontal Scaling** – Run multiple agent instances behind a load balancer. Ensure task store supports concurrency (Redis, SQL, Firestore).
- **Autoscaling** – Base scaling policies on CPU, memory, or custom metrics (active tasks). For streaming workloads, consider scaling on number of open connections.
- **Multi-Region Deployments** – Host agents closer to users to reduce latency. Replicate task stores or use global databases.
- **Capacity Planning** – Benchmark representative scenarios (LangGraph loops, MCP bridge, image generation). Track CPU, GPU, memory, and token usage to set quotas.

## 5. Operations Runbooks

Create concise runbooks stored alongside the guides:

- **On-call Checklist** – Steps to verify service health, restart components, and consult metrics dashboards.
- **Incident Response** – Link to Guide 6’s playbook plus service-specific remediation steps.
- **Upgrade Guide** – Describe how to bump SDK versions, re-run Inspector validations, and update extensions.
- **Disaster Recovery** – Document backups for task stores, artifacts, and configuration. Test restore procedures periodically.

## 6. Compliance & Governance

- Maintain an inventory of extensions and their data handling characteristics (PII, telemetry, debug info).
- Align retention policies: e.g., keep trace data for 30 days, transcripts for 7 days, artifacts per policy.
- Provide transparency reports to partners outlining uptime, incidents, and upcoming changes.

## 7. Documentation & Change Management

- Update the relevant guide and changelog whenever you introduce a new extension, deployment strategy, or operational control.
- Record Inspector traces, load-test results, and security assessment notes for each release.
- Encourage contributors to attach `a2a-inspector` logs and sample commands to pull requests (reinforced in `AGENTS.md`).

## 8. Production Checklist

- [ ] AgentCard lists supported extensions with accurate versions.
- [ ] Automated tests validate extension behaviour (timestamps present, trace IDs propagated, etc.).
- [ ] Observability stack captures metrics, logs, and traces with retention policies defined.
- [ ] Deployment pipeline includes canary or blue/green strategy with rollback steps.
- [ ] Runbooks published and linked from README or internal portal.
- [ ] Regular audits of task store backups and artifact retention.

With extension support, disciplined deployments, and robust operations, your agents become reliable building blocks for partner ecosystems and mission-critical workflows.
