"""Fix: Flask debug mode is off by default and controlled by FLASK_DEBUG.

The Werkzeug debugger allows arbitrary code execution from a browser. It must
never be on unless someone sets FLASK_DEBUG=1 for local development.
"""

import pytest

import app as app_module


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_flask_debug_is_on_for_true_values(monkeypatch, value):
    monkeypatch.setenv("FLASK_DEBUG", value)
    assert app_module.env_flag("FLASK_DEBUG") is True


@pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "anything-else"])
def test_flask_debug_is_off_for_other_values(monkeypatch, value):
    monkeypatch.setenv("FLASK_DEBUG", value)
    assert app_module.env_flag("FLASK_DEBUG") is False


def test_flask_debug_is_off_when_unset(monkeypatch):
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    assert app_module.env_flag("FLASK_DEBUG") is False


def test_app_object_is_not_in_debug_mode_by_default():
    assert app_module.app.debug is False
