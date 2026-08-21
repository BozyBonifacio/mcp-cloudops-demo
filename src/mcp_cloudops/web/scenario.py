from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    name: str
    service: str | None = None
    server_name: str | None = None
    environment: str | None = None
    severity: str | None = None
    confirmed: bool = False


def classify_message(message: str) -> Intent:
    """Classify a small set of deterministic demo intents without an external LLM."""
    text = message.strip().lower()

    service = None
    if "payments-api" in text or "payment" in text:
        service = "payments-api"
    elif "invoice-worker" in text or "invoice" in text:
        service = "invoice-worker"

    server_name = None
    for candidate in ("api-prod-01", "api-prod-02", "worker-stg-01"):
        if candidate in text:
            server_name = candidate
            break

    environment = None
    if "production" in text or " prod" in f" {text}":
        environment = "prod"
    elif "staging" in text or " stg" in f" {text}":
        environment = "stg"

    severity = None
    if "error" in text:
        severity = "ERROR"
    elif "warn" in text:
        severity = "WARN"

    confirmed = "confirm" in text or "confirmed" in text

    if "restart" in text:
        return Intent("restart", service, server_name, environment, severity, confirmed)
    if "incident" in text or "investigate" in text or "root cause" in text or "likely cause" in text:
        return Intent("incident", service or "payments-api", server_name, environment, severity, confirmed)
    if "deployment" in text or "deploy" in text:
        return Intent("deployments", service or "payments-api", server_name, environment, severity, confirmed)
    if "log" in text:
        return Intent("logs", service or "payments-api", server_name, environment, severity, confirmed)
    if "unhealthy" in text or "degraded" in text or "resource pressure" in text or "health" in text:
        return Intent("health", service, server_name, environment or "prod", severity, confirmed)
    if "server" in text or "inventory" in text:
        return Intent("servers", service, server_name, environment, severity, confirmed)
    if "resource" in text:
        return Intent("resources", service, server_name, environment, severity, confirmed)
    if "prompt" in text:
        return Intent("prompts", service, server_name, environment, severity, confirmed)

    return Intent("help", service, server_name, environment, severity, confirmed)
