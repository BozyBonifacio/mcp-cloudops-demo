from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt()
    def investigate_incident(service: str) -> str:
        """Guide an MCP client through a structured CloudOps incident investigation."""
        return f"""Investigate the service '{service}' using the available MCP capabilities.

1. Check open incidents for the service.
2. Identify servers running the service and inspect their health.
3. Review recent deployments.
4. Search WARN and ERROR logs.
5. Correlate timing across incidents, deployments, metrics, and logs.
6. Summarize the most likely cause and provide safe next steps.
7. Do not run restart_demo_service unless the user explicitly requests a simulated restart.
"""

    @mcp.prompt()
    def daily_cloudops_summary(environment: str = "prod") -> str:
        """Generate instructions for a concise environment health summary."""
        return f"""Create a CloudOps summary for environment '{environment}'.
Use MCP tools/resources to report degraded servers, utilization hotspots,
open incidents, and recent failed deployments. Keep the output concise and
separate observed facts from recommendations.
"""
