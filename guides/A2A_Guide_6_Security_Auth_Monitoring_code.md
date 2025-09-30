# Guide 6 · Python Code Samples

```python
"""Security, authentication, and monitoring helpers for Guide 6."""

from __future__ import annotations

import asyncio
import base64
import dataclasses
import datetime as dt
import hashlib
import json
import logging
import os
import random
import secrets
import string
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

LOG = logging.getLogger("guide6")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Agent security configuration helpers
# ---------------------------------------------------------------------------

@dataclass
class SecurityScheme:
    scheme: str
    location: str
    name: str
    description: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "scheme": self.scheme,
            "in": self.location,
            "name": self.name,
            "description": self.description,
        }


def build_security_block() -> list[dict[str, Any]]:
    return [
        SecurityScheme("api_key", "header", "X-API-Key", "Provisioned per host; rotate every 30 days.").as_dict(),
        {
            "scheme": "oauth2",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "https://idp.example.com/token",
                    "scopes": {"agent.read": "Read-only access"},
                }
            },
        },
    ]


# ---------------------------------------------------------------------------
# Sanitisation and validation
# ---------------------------------------------------------------------------

ALLOWED_TAGS = {"b", "i", "code", "strong"}


def sanitize_text(text: str) -> str:
    for tag in ["<", ">"]:
        text = text.replace(tag, "")
    return text


def sanitize_agent_card(card: dict[str, Any]) -> dict[str, Any]:
    card = dict(card)
    card["description"] = sanitize_text(card.get("description", ""))
    for skill in card.get("skills", []):
        skill["description"] = sanitize_text(skill.get("description", ""))
    return card


def validate_payload(payload: dict[str, Any]) -> None:
    if "input" not in payload or "text" not in payload["input"]:
        raise ValueError("Invalid payload structure")
    if len(payload["input"]["text"]) > 4000:
        raise ValueError("Input text too long")


# ---------------------------------------------------------------------------
# Rate limiting and throttling
# ---------------------------------------------------------------------------

REQUEST_HISTORY: dict[str, list[float]] = defaultdict(list)


def allow_request(client_id: str, limit: int = 30, window_seconds: int = 60) -> bool:
    now = dt.datetime.utcnow().timestamp()
    history = [timestamp for timestamp in REQUEST_HISTORY[client_id] if now - timestamp < window_seconds]
    REQUEST_HISTORY[client_id] = history
    if len(history) >= limit:
        return False
    REQUEST_HISTORY[client_id].append(now)
    return True


# ---------------------------------------------------------------------------
# Credential generation and storage
# ---------------------------------------------------------------------------

def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def store_secret(path: Path, key: str) -> None:
    path.write_text(key, encoding="utf-8")
    path.chmod(0o600)


# ---------------------------------------------------------------------------
# JWT validation stub
# ---------------------------------------------------------------------------

SECRET_KEY = "dummy-secret"


def sign_token(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True).encode()
    signature = hashlib.sha256(data + SECRET_KEY.encode()).hexdigest()
    return base64.urlsafe_b64encode(data).decode() + "." + signature


def verify_token(token: str) -> dict[str, Any]:
    encoded, signature = token.split(".")
    data = base64.urlsafe_b64decode(encoded.encode())
    expected = hashlib.sha256(data + SECRET_KEY.encode()).hexdigest()
    if not secrets.compare_digest(signature, expected):
        raise ValueError("Invalid signature")
    return json.loads(data)


# ---------------------------------------------------------------------------
# Artifact validation
# ---------------------------------------------------------------------------

ALLOWED_MIME = {"application/pdf", "image/png"}
MAX_SIZE = 5 * 1024 * 1024


def validate_artifact(filename: str, mime: str, data: bytes) -> None:
    if mime not in ALLOWED_MIME:
        raise ValueError("Unsupported MIME type")
    if len(data) > MAX_SIZE:
        raise ValueError("Artifact too large")
    if not filename:
        raise ValueError("Filename required")


# ---------------------------------------------------------------------------
# Monitoring and telemetry
# ---------------------------------------------------------------------------

@dataclass
class MetricSample:
    value: float
    timestamp: dt.datetime


@dataclass
class MetricStream:
    samples: list[MetricSample] = field(default_factory=list)

    def observe(self, value: float) -> None:
        self.samples.append(MetricSample(value, dt.datetime.utcnow()))

    def average(self) -> float:
        return sum(sample.value for sample in self.samples) / len(self.samples) if self.samples else 0.0


@dataclass
class TelemetryRecorder:
    metrics: dict[str, MetricStream] = field(default_factory=dict)

    def record(self, name: str, value: float) -> None:
        stream = self.metrics.setdefault(name, MetricStream())
        stream.observe(value)

    def export(self) -> dict[str, float]:
        return {name: stream.average() for name, stream in self.metrics.items()}


# ---------------------------------------------------------------------------
# Incident response playbook in Python structures
# ---------------------------------------------------------------------------

INCIDENT_PLAYBOOK = [
    {"verify_alert": True},
    {"identify_scope": True},
    {"revoke_credentials": True},
    {"notify_stakeholders": True},
    {"document_timeline": True},
]


# ---------------------------------------------------------------------------
# Risk assessment matrix as Python dict
# ---------------------------------------------------------------------------

RISK_MATRIX = {
    "prompt_injection": {"likelihood": "medium", "impact": "high"},
    "credential_leak": {"likelihood": "low", "impact": "critical"},
}


# ---------------------------------------------------------------------------
# Data retention policy representation
# ---------------------------------------------------------------------------

RETENTION_POLICY = {
    "transcripts": dt.timedelta(days=7),
    "artifacts": dt.timedelta(days=30),
    "audit_logs": dt.timedelta(days=90),
}


def purge_records(records: list[dict[str, Any]], policy_key: str) -> list[dict[str, Any]]:
    window = RETENTION_POLICY[policy_key]
    cutoff = dt.datetime.utcnow() - window
    return [record for record in records if dt.datetime.fromisoformat(record["timestamp"]) >= cutoff]


# ---------------------------------------------------------------------------
# Security alerts and SIEM integration stubs
# ---------------------------------------------------------------------------

ALERT_THRESHOLDS = {"task_failure": 10, "auth_failure": 3}


def should_alert(metric: str, count: int) -> bool:
    return count >= ALERT_THRESHOLDS.get(metric, 0)


def send_security_event(event: dict[str, Any]) -> None:
    LOG.info("Sending security event: %s", event)


# ---------------------------------------------------------------------------
# Anomaly detection helpers
# ---------------------------------------------------------------------------

TASK_COUNTER = Counter()


def record_task(agent_id: str) -> None:
    TASK_COUNTER[agent_id] += 1


def detect_high_volume(threshold: int = 100) -> list[str]:
    return [agent for agent, count in TASK_COUNTER.items() if count > threshold]


# ---------------------------------------------------------------------------
# Backup and restore simulation
# ---------------------------------------------------------------------------

BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)


def create_backup(filename: str, data: dict[str, Any]) -> Path:
    path = BACKUP_DIR / filename
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    LOG.info("Backup stored at %s", path)
    return path


def restore_backup(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Token redaction utilities
# ---------------------------------------------------------------------------

SENSITIVE_KEYS = {"api_key", "token", "password"}


def redact_metadata(metadata: dict[str, str]) -> dict[str, str]:
    return {
        key: ("***" if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS) else value)
        for key, value in metadata.items()
    }


# ---------------------------------------------------------------------------
# Security logging helpers
# ---------------------------------------------------------------------------

@dataclass
class AuditLog:
    path: Path

    def append(self, event: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# Inspector trace validation stubs
# ---------------------------------------------------------------------------

async def validate_trace(transcript: list[dict[str, str]]) -> bool:
    await asyncio.sleep(0.01)
    return all(entry.get("text") for entry in transcript)


# ---------------------------------------------------------------------------
# Security checklist generation
# ---------------------------------------------------------------------------

def security_checklist() -> list[str]:
    return [
        "Validate AgentCard security block",
        "Rotate API keys",
        "Scan dependencies",
        "Review audit logs",
        "Run inspector validation",
    ]


# ---------------------------------------------------------------------------
# Token generation for partners
# ---------------------------------------------------------------------------

@dataclass
class PartnerToken:
    partner_id: str
    token: str
    expires_at: dt.datetime


def issue_partner_token(partner_id: str, hours_valid: int = 1) -> PartnerToken:
    token = generate_api_key()
    expires = dt.datetime.utcnow() + dt.timedelta(hours=hours_valid)
    return PartnerToken(partner_id, token, expires)


# ---------------------------------------------------------------------------
# Alert manager stub
# ---------------------------------------------------------------------------

@dataclass
class Alert:
    severity: str
    message: str
    timestamp: dt.datetime


@dataclass
class AlertManager:
    alerts: list[Alert] = field(default_factory=list)

    def record(self, severity: str, message: str) -> None:
        self.alerts.append(Alert(severity, message, dt.datetime.utcnow()))
        LOG.warning("Alert [%s]: %s", severity, message)

    def summarize(self) -> dict[str, int]:
        counts = Counter(alert.severity for alert in self.alerts)
        return dict(counts)


# ---------------------------------------------------------------------------
# Data loss prevention (DLP) checks
# ---------------------------------------------------------------------------

DLP_KEYWORDS = {"password", "secret", "credential"}


def enforce_dlp(text: str) -> None:
    lowered = text.lower()
    if any(keyword in lowered for keyword in DLP_KEYWORDS):
        raise ValueError("Sensitive keyword detected")


# ---------------------------------------------------------------------------
# Synthetic security posture report
# ---------------------------------------------------------------------------

@dataclass
class SecurityReport:
    timestamp: dt.datetime
    checklist_completed: bool
    risk_summary: dict[str, Any]

    def as_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2, default=str)


# ---------------------------------------------------------------------------
# Inline tests for utilities
# ---------------------------------------------------------------------------

def _test_redact_metadata() -> None:
    meta = {"api_key": "abc", "user": "alice"}
    redacted = redact_metadata(meta)
    assert redacted["api_key"] == "***"
    assert redacted["user"] == "alice"


def _test_token_issue() -> None:
    token = issue_partner_token("partner")
    assert token.partner_id == "partner"


def _test_allow_request() -> None:
    client = "client-a"
    for _ in range(30):
        assert allow_request(client)
    assert not allow_request(client)


# ---------------------------------------------------------------------------
# Comprehensive demo orchestrating utilities
# ---------------------------------------------------------------------------

async def run_security_demo() -> SecurityReport:
    LOG.info("Starting security demo")
    key = generate_api_key()
    store_secret(Path("secret.key"), key)
    payload = {"input": {"text": "Run security check"}}
    validate_payload(payload)
    card = sanitize_agent_card({"description": "<b>Agent</b>", "skills": [{"description": "<script>"}]})
    LOG.info("Sanitized card %s", card)
    recorder = TelemetryRecorder()
    recorder.record("latency_ms", random.uniform(100, 200))
    recorder.record("latency_ms", random.uniform(90, 150))
    checklist = security_checklist()
    alerts = AlertManager()
    alerts.record("warning", "High failure rate")
    report = SecurityReport(
        timestamp=dt.datetime.utcnow(),
        checklist_completed=False,
        risk_summary={"alerts": alerts.summarize(), "metrics": recorder.export()},
    )
    LOG.info("Security report %s", report.as_json())
    return report


if __name__ == "__main__":
    asyncio.run(run_security_demo())
```

```python
"""Supplementary monitoring utilities."""

from __future__ import annotations

import shutil
from itertools import islice

# ---------------------------------------------------------------------------
# Log rotation
# ---------------------------------------------------------------------------

@dataclass
class LogRotator:
    directory: Path
    basename: str
    max_files: int

    def rotate(self, new_entry: str) -> None:
        file = self.directory / f"{self.basename}.log"
        entries = []
        if file.exists():
            entries = file.read_text(encoding="utf-8").splitlines()
        entries.append(new_entry)
        file.write_text("\n".join(entries[-self.max_files :]), encoding="utf-8")


# ---------------------------------------------------------------------------
# Disk usage reporting
# ---------------------------------------------------------------------------

def disk_usage(path: Path) -> dict[str, int]:
    total, used, free = shutil.disk_usage(path)
    return {"total": total, "used": used, "free": free}


# ---------------------------------------------------------------------------
# Privacy filter utilities
# ---------------------------------------------------------------------------

@dataclass
class PrivacyFilter:
    blocked_domains: set[str]

    def filter_urls(self, text: str) -> str:
        for domain in self.blocked_domains:
            text = text.replace(domain, "[blocked]")
        return text


# ---------------------------------------------------------------------------
# Sliding window statistics
# ---------------------------------------------------------------------------

@dataclass
class SlidingWindow:
    size: int
    values: list[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        self.values.append(value)
        if len(self.values) > self.size:
            self.values.pop(0)

    def average(self) -> float:
        return sum(self.values) / len(self.values) if self.values else 0.0


# ---------------------------------------------------------------------------
# Command execution tracker
# ---------------------------------------------------------------------------

@dataclass
class CommandTracker:
    commands: list[str] = field(default_factory=list)

    def record(self, command: str) -> None:
        self.commands.append(command)

    def recent(self, count: int = 5) -> list[str]:
        return list(islice(reversed(self.commands), 0, count))


# ---------------------------------------------------------------------------
# Additional inline tests
# ---------------------------------------------------------------------------

def _test_privacy_filter() -> None:
    flt = PrivacyFilter({"example.com"})
    assert "[blocked]" in flt.filter_urls("visit example.com")


def _test_sliding_window() -> None:
    window = SlidingWindow(3)
    window.add(1)
    window.add(2)
    window.add(3)
    window.add(4)
    assert window.average() == (2 + 3 + 4) / 3


def _test_log_rotator(tmp_path: Path) -> None:
    rotator = LogRotator(tmp_path, "audit", 2)
    rotator.rotate("line1")
    rotator.rotate("line2")
    rotator.rotate("line3")
    content = (tmp_path / "audit.log").read_text(encoding="utf-8")
    assert "line1" not in content


if __name__ == "__main__":
    _test_privacy_filter()
    _test_sliding_window()
```
