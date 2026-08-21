from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_cloudops.store import load_json


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def list_servers(environment: str | None = None) -> list[dict[str, Any]]:
        """List demo servers, optionally filtering by environment such as prod or stg."""
        servers = load_json("servers.json")
        if environment:
            servers = [s for s in servers if s["environment"].lower() == environment.lower()]
        return servers

    @mcp.tool()
    def get_server_health(server_name: str) -> dict[str, Any]:
        """Return health and utilization metrics for a demo server."""
        for server in load_json("servers.json"):
            if server["name"].lower() == server_name.lower():
                return server
        return {"error": f"Server '{server_name}' was not found"}

    @mcp.tool()
    def get_recent_deployments(
        service: str | None = None,
        server_name: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return recent demo deployments, optionally filtered by service or server."""
        deployments = load_json("deployments.json")
        if service:
            deployments = [d for d in deployments if d["service"].lower() == service.lower()]
        if server_name:
            deployments = [d for d in deployments if d["server"].lower() == server_name.lower()]
        deployments.sort(key=lambda d: d["deployed_at"], reverse=True)
        return deployments[: max(1, min(limit, 20))]

    @mcp.tool()
    def get_open_incidents(service: str | None = None) -> list[dict[str, Any]]:
        """Return open incidents, optionally filtered by service."""
        incidents = [i for i in load_json("incidents.json") if i["status"] == "open"]
        if service:
            incidents = [i for i in incidents if i["service"].lower() == service.lower()]
        return incidents

    @mcp.tool()
    def search_logs(
        service: str | None = None,
        server_name: str | None = None,
        severity: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search deterministic demo logs by service, server, or severity."""
        logs = load_json("logs.json")
        if service:
            logs = [x for x in logs if x["service"].lower() == service.lower()]
        if server_name:
            logs = [x for x in logs if x["server"].lower() == server_name.lower()]
        if severity:
            logs = [x for x in logs if x["severity"].lower() == severity.lower()]
        return logs

    @mcp.tool()
    def restart_demo_service(server_name: str, confirmed: bool = False) -> dict[str, Any]:
        """Simulate a restart. Requires confirmed=true and never touches real infrastructure."""
        known = {s["name"] for s in load_json("servers.json")}
        if server_name not in known:
            return {"ok": False, "message": f"Server '{server_name}' was not found"}
        if not confirmed:
            return {
                "ok": False,
                "requires_confirmation": True,
                "message": "Simulation only. Call again with confirmed=true to perform the demo action.",
            }
        return {
            "ok": True,
            "simulated": True,
            "server": server_name,
            "message": "Demo restart completed. No real cloud resource was changed.",
        }
