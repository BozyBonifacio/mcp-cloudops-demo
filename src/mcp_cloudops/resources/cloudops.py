from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from mcp_cloudops.store import load_json


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource("infra://inventory/all")
    def inventory() -> str:
        """Complete demo infrastructure inventory."""
        return json.dumps(load_json("servers.json"), indent=2)

    @mcp.resource("infra://inventory/production")
    def production_inventory() -> str:
        """Production-only demo infrastructure inventory."""
        servers = [s for s in load_json("servers.json") if s["environment"] == "prod"]
        return json.dumps(servers, indent=2)

    @mcp.resource("ops://incidents/open")
    def open_incidents() -> str:
        """Open demo incidents as an MCP resource."""
        incidents = [i for i in load_json("incidents.json") if i["status"] == "open"]
        return json.dumps(incidents, indent=2)
