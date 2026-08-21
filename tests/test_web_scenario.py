from mcp_cloudops.web.scenario import classify_message


def test_incident_prompt_is_classified():
    intent = classify_message("Investigate the open incident affecting payments-api")
    assert intent.name == "incident"
    assert intent.service == "payments-api"


def test_health_prompt_defaults_to_prod():
    intent = classify_message("Which production servers are unhealthy?")
    assert intent.name == "health"
    assert intent.environment == "prod"


def test_restart_requires_explicit_confirmation_word():
    pending = classify_message("Restart api-prod-02")
    confirmed = classify_message("Confirm restart api-prod-02")
    assert pending.name == "restart"
    assert pending.confirmed is False
    assert confirmed.confirmed is True
