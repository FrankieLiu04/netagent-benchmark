from __future__ import annotations

import sys

from netagent.config import Settings
from netagent.mcp_client import cml_mcp_params


def test_cml_mcp_params_uses_python_with_cml_mcp_module():
    settings = Settings(
        deepseek_api_key="key",
        cml_url="https://cml.example",
        cml_username="user",
        cml_password="pass",
    )

    params = cml_mcp_params(settings)
    assert params.command == sys.executable
    assert params.args == ["-m", "cml_mcp"]
