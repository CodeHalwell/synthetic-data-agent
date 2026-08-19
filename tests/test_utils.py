"""Offline unit tests for utils: config loading, DB config, and resilience."""

import asyncio

import pytest
from google.genai import types

from utils.config import load_config, retry_config
from utils.db import create_db_engine, get_database_url
from utils.resilience import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    retry_with_backoff,
)

# ---------------------------------------------------------------------------
# utils.config
# ---------------------------------------------------------------------------


def test_load_config_reads_yaml(tmp_path):
    config_file = tmp_path / "agent.yaml"
    config_file.write_text("name: test_agent\nmodel: gemini-test\n", encoding="utf-8")

    config = load_config(config_file)
    assert config == {"name": "test_agent", "model": "gemini-test"}


def test_retry_config_returns_http_retry_options():
    options = retry_config()
    assert isinstance(options, types.HttpRetryOptions)
    assert options.attempts == 5
    assert 429 in options.http_status_codes


# ---------------------------------------------------------------------------
# utils.db
# ---------------------------------------------------------------------------


def test_database_url_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/override.db")
    assert get_database_url() == f"sqlite:///{tmp_path}/override.db"


def test_create_db_engine_creates_all_tables(tmp_path):
    from sqlalchemy import inspect

    engine = create_db_engine(f"sqlite:///{tmp_path}/fresh.db")
    tables = set(inspect(engine).get_table_names())
    assert "questions" in tables
    assert "synthetic_data_sft" in tables
    assert len(tables) == 10  # questions + 9 training-type tables


# ---------------------------------------------------------------------------
# utils.resilience
# ---------------------------------------------------------------------------


def test_retry_with_backoff_sync_retries_until_success():
    calls = {"count": 0}

    @retry_with_backoff(max_attempts=3, initial_delay=0.01, max_delay=0.02)
    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("transient")
        return "ok"

    assert flaky() == "ok"
    assert calls["count"] == 3


def test_retry_with_backoff_sync_raises_after_max_attempts():
    @retry_with_backoff(max_attempts=2, initial_delay=0.01, max_delay=0.02)
    def always_fails():
        raise ValueError("permanent")

    with pytest.raises(ValueError, match="permanent"):
        always_fails()


async def test_retry_with_backoff_async_retries_until_success():
    calls = {"count": 0}

    @retry_with_backoff(max_attempts=3, initial_delay=0.01, max_delay=0.02)
    async def flaky():
        calls["count"] += 1
        if calls["count"] < 2:
            raise ValueError("transient")
        return "ok"

    assert await flaky() == "ok"
    assert calls["count"] == 2


def test_circuit_breaker_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

    def boom():
        raise RuntimeError("service down")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            breaker.call(boom)

    assert breaker.state is CircuitState.OPEN
    with pytest.raises(CircuitBreakerOpenError):
        breaker.call(boom)


def test_circuit_breaker_recovers_after_timeout():
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

    with pytest.raises(RuntimeError):
        breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))
    assert breaker.state is CircuitState.OPEN

    # recovery_timeout=0 means the next call goes to HALF_OPEN and can close
    assert breaker.call(lambda: "recovered") == "recovered"
    assert breaker.state is CircuitState.CLOSED


async def test_circuit_breaker_async_call():
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60)

    async def ok():
        await asyncio.sleep(0)
        return 42

    assert await breaker.call_async(ok) == 42
