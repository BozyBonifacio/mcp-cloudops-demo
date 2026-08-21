from mcp_cloudops.store import load_json


def test_deployments_reference_known_servers() -> None:
    servers = {s["name"] for s in load_json("servers.json")}
    for deployment in load_json("deployments.json"):
        assert deployment["server"] in servers


def test_logs_reference_known_servers() -> None:
    servers = {s["name"] for s in load_json("servers.json")}
    for log in load_json("logs.json"):
        assert log["server"] in servers
