from __future__ import annotations

import sys

from fyp_agent.config import Settings
from fyp_agent.mcp_client import _COMPAT_LAUNCHER, cml_mcp_params


def test_cml_mcp_params_uses_python_with_compat_launcher():
    """验证 cml_mcp_params 使用当前 venv 的 Python 启动 _cml_compat.py。"""
    settings = Settings(
        deepseek_api_key="key",
        cml_url="https://cml.example",
        cml_username="user",
        cml_password="pass",
    )

    params = cml_mcp_params(settings)
    assert params["command"] == sys.executable
    assert params["args"] == [str(_COMPAT_LAUNCHER)]
