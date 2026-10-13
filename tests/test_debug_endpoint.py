"""Fix: /debug is off unless ENABLE_DEBUG_ENDPOINT is set.

The route returns paths, memory and disk use, and library versions. Anyone who
could reach the server could read them before this fix.
"""

import pytest


@pytest.fixture
def no_debug_env(monkeypatch):
    monkeypatch.delenv("ENABLE_DEBUG_ENDPOINT", raising=False)


def test_debug_endpoint_is_hidden_by_default(client, no_debug_env):
    response = client.get("/debug")
    assert response.status_code == 404
    assert b"python_version" not in response.data


@pytest.mark.parametrize("value", ["0", "false", "no", ""])
def test_debug_endpoint_stays_hidden_for_false_values(client, monkeypatch, value):
    monkeypatch.setenv("ENABLE_DEBUG_ENDPOINT", value)
    assert client.get("/debug").status_code == 404


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_debug_endpoint_is_served_when_enabled(client, monkeypatch, value):
    monkeypatch.setenv("ENABLE_DEBUG_ENDPOINT", value)
    response = client.get("/debug")
    assert response.status_code == 200
    assert "python_version" in response.get_json()
