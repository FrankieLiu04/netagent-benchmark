from __future__ import annotations

from fyp_agent.config import Settings
from fyp_agent.mcp_client import cml_mcp_params


def test_cml_mcp_params_pin_supported_python():
    settings = Settings(
        deepseek_api_key="key",
        cml_url="https://cml.example",
        cml_username="user",
        cml_password="pass",
        mcp_python="3.13",
    )

    params = cml_mcp_params(settings)
    assert params["command"] == "uvx"
    assert params["args"] == ["--python", "3.13", "cml-mcp[pyats]"]
