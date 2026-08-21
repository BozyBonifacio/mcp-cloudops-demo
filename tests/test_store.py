from mcp_cloudops.store import load_json


def test_server_fixture_contains_degraded_node() -> None:
    servers = load_json("servers.json")
    degraded = [s for s in servers if s["status"] == "degraded"]
    assert degraded
    assert degraded[0]["cpu_percent"] >= 90


def test_incident_fixture_has_open_incident() -> None:
    incidents = load_json("incidents.json")
    assert any(i["status"] == "open" for i in incidents)
