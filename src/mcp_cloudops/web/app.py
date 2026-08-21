from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field

from mcp_cloudops.web.scenario import Intent, classify_message

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="MCP CloudOps Browser Demo",
    description="A browser UI that acts as an MCP client for the local CloudOps MCP server.",
    version="0.2.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class TraceItem(BaseModel):
    kind: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    answer: str
    trace: list[TraceItem]
    intent: str


def _content_to_python(result: Any) -> Any:
    """Convert MCP text content into Python data when the server returned JSON."""
    content = getattr(result, "content", [])
    texts = [item.text for item in content if hasattr(item, "text")]
    if texts:
        text = "\n".join(texts)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    structured = getattr(result, "structuredContent", None) or getattr(
        result, "structured_content", None
    )
    return structured


@asynccontextmanager
async def mcp_session() -> AsyncIterator[ClientSession]:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_cloudops.server"],
    )
    async with stdio_client(params) as (read_stream, write_stream), ClientSession(
        read_stream, write_stream
    ) as session:
        await session.initialize()
        yield session


async def _call(
    session: ClientSession,
    trace: list[TraceItem],
    name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    args = arguments or {}
    trace.append(TraceItem(kind="tool", name=name, arguments=args))
    result = await session.call_tool(name, arguments=args)
    return _content_to_python(result)


def _server_line(server: dict[str, Any]) -> str:
    return (
        f"{server['name']} — {server['status']} | CPU {server['cpu_percent']}% | "
        f"Memory {server['memory_percent']}% | {server['service']}"
    )


def _format_incident_answer(
    incidents: list[dict[str, Any]],
    servers: list[dict[str, Any]],
    deployments: list[dict[str, Any]],
    logs: list[dict[str, Any]],
    service: str,
) -> str:
    affected = [s for s in servers if s.get("service") == service and s.get("status") != "healthy"]
    incident = incidents[0] if incidents else None
    affected_server = affected[0] if affected else None

    lines = [f"Investigation summary for {service}", ""]
    if incident:
        lines.append(
            f"Incident: {incident['id']} ({incident['severity']}) — {incident['summary']} "
            f"started at {incident['started_at']}."
        )
    else:
        lines.append("No open incident was found for this service.")

    if affected_server:
        lines.append(f"Affected server: {_server_line(affected_server)}.")
    else:
        lines.append("No degraded server was found for this service.")

    if deployments:
        newest = deployments[0]
        lines.append(
            f"Recent deployment: {newest['id']} version {newest['version']} to "
            f"{newest['server']} at {newest['deployed_at']} ({newest['status']})."
        )

    if logs:
        lines.append("Relevant logs:")
        for entry in logs[:4]:
            lines.append(f"• {entry['timestamp']} [{entry['severity']}] {entry['server']}: {entry['message']}")

    if incident and affected_server and deployments and logs:
        lines.extend(
            [
                "",
                (
                    "Likely cause: the evidence points to resource saturation on api-prod-02 after the "
                    "2.7.1 deployment. The deployment itself completed successfully, but the incident "
                    "began shortly afterwards and the node reports CPU above 90% plus excessive request queue depth."
                ),
                "",
                (
                    "Safe next steps: compare api-prod-01 vs api-prod-02, inspect workload/request distribution, "
                    "review changes in commit 7f3ac11, and validate capacity before considering the simulated restart action."
                ),
            ]
        )

    return "\n".join(lines)


async def _run_intent(session: ClientSession, intent: Intent, trace: list[TraceItem]) -> str:
    if intent.name == "incident":
        service = intent.service or "payments-api"
        incidents = await _call(session, trace, "get_open_incidents", {"service": service}) or []
        servers = await _call(session, trace, "list_servers", {"environment": "prod"}) or []
        deployments = await _call(
            session, trace, "get_recent_deployments", {"service": service, "limit": 5}
        ) or []
        logs = await _call(session, trace, "search_logs", {"service": service}) or []
        return _format_incident_answer(incidents, servers, deployments, logs, service)

    if intent.name == "health":
        if intent.server_name:
            server = await _call(
                session, trace, "get_server_health", {"server_name": intent.server_name}
            )
            return _server_line(server) if isinstance(server, dict) and "name" in server else str(server)
        servers = await _call(
            session, trace, "list_servers", {"environment": intent.environment or "prod"}
        ) or []
        pressured = [
            s for s in servers
            if s.get("status") != "healthy" or s.get("cpu_percent", 0) >= 80 or s.get("memory_percent", 0) >= 80
        ]
        if not pressured:
            return "No unhealthy or high-pressure servers were found."
        return "Servers needing attention:\n" + "\n".join(f"• {_server_line(s)}" for s in pressured)

    if intent.name == "servers":
        args = {"environment": intent.environment} if intent.environment else {}
        servers = await _call(session, trace, "list_servers", args) or []
        return "Demo inventory:\n" + "\n".join(f"• {_server_line(s)}" for s in servers)

    if intent.name == "deployments":
        args: dict[str, Any] = {"limit": 5}
        if intent.service:
            args["service"] = intent.service
        if intent.server_name:
            args["server_name"] = intent.server_name
        deployments = await _call(session, trace, "get_recent_deployments", args) or []
        if not deployments:
            return "No matching deployments were found."
        return "Recent deployments:\n" + "\n".join(
            f"• {d['id']} | {d['service']} {d['version']} → {d['server']} | {d['status']} | {d['deployed_at']}"
            for d in deployments
        )

    if intent.name == "logs":
        args = {}
        if intent.service:
            args["service"] = intent.service
        if intent.server_name:
            args["server_name"] = intent.server_name
        if intent.severity:
            args["severity"] = intent.severity
        logs = await _call(session, trace, "search_logs", args) or []
        if not logs:
            return "No matching demo logs were found."
        return "Matching logs:\n" + "\n".join(
            f"• {x['timestamp']} [{x['severity']}] {x['server']}: {x['message']}" for x in logs
        )

    if intent.name == "restart":
        server_name = intent.server_name or "api-prod-02"
        result = await _call(
            session,
            trace,
            "restart_demo_service",
            {"server_name": server_name, "confirmed": intent.confirmed},
        )
        if isinstance(result, dict):
            return result.get("message", json.dumps(result, indent=2))
        return str(result)

    if intent.name == "resources":
        resources = await session.list_resources()
        trace.append(TraceItem(kind="discovery", name="resources/list"))
        items = [str(resource.uri) for resource in resources.resources]
        return "Available MCP resources:\n" + "\n".join(f"• {x}" for x in items)

    if intent.name == "prompts":
        prompts = await session.list_prompts()
        trace.append(TraceItem(kind="discovery", name="prompts/list"))
        return "Available MCP prompts:\n" + "\n".join(f"• {p.name}" for p in prompts.prompts)

    tools = await session.list_tools()
    trace.append(TraceItem(kind="discovery", name="tools/list"))
    names = ", ".join(tool.name for tool in tools.tools)
    return (
        "I am a deterministic portfolio UI, so no paid LLM/API key is required. "
        "Try one of the suggested prompts below. The backend is a real MCP client and currently discovered: "
        f"{names}."
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "mode": "browser-mcp-client"}


@app.get("/api/capabilities")
async def capabilities() -> dict[str, list[str]]:
    async with mcp_session() as session:
        tools = await session.list_tools()
        resources = await session.list_resources()
        prompts = await session.list_prompts()
        return {
            "tools": [tool.name for tool in tools.tools],
            "resources": [str(resource.uri) for resource in resources.resources],
            "prompts": [prompt.name for prompt in prompts.prompts],
        }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    trace: list[TraceItem] = []
    intent = classify_message(request.message)
    async with mcp_session() as session:
        answer = await _run_intent(session, intent, trace)
    return ChatResponse(answer=answer, trace=trace, intent=intent.name)


def main() -> None:
    import uvicorn

    uvicorn.run("mcp_cloudops.web.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
