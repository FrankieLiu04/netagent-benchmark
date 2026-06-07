from __future__ import annotations

import pytest

from fyp_agent.config import ConfigError, Settings, load_settings


def test_missing_env_has_clear_error(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("CML_URL", raising=False)
    monkeypatch.delenv("CML_USERNAME", raising=False)
    monkeypatch.delenv("CML_PASSWORD", raising=False)

    with pytest.raises(ConfigError) as exc_info:
        load_settings(tmp_path / "missing.env")

    message = str(exc_info.value)
    assert "Agent configuration is incomplete" in message
    assert "cml_url" in message
    assert "cml_username" in message


def test_missing_deepseek_key_has_clear_error(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "LLM_PROVIDER=deepseek",
                "CML_URL=https://cml.example",
                "CML_USERNAME=user",
                "CML_PASSWORD=pass",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(ConfigError) as exc_info:
        load_settings(env_file)

    assert "DEEPSEEK_API_KEY is required" in str(exc_info.value)


def test_cml_verify_ssl_false_is_parsed_as_bool():
    settings = Settings(
        deepseek_api_key="key",
        cml_url="https://cml.example",
        cml_username="user",
        cml_password="pass",
        cml_verify_ssl="false",
    )

    assert settings.cml_verify_ssl is False
    assert settings.cml_env()["CML_VERIFY_SSL"] == "false"


def test_deepseek_defaults_are_selected():
    settings = Settings(
        deepseek_api_key="key",
        cml_url="https://cml.example",
        cml_username="user",
        cml_password="pass",
    )

    assert settings.llm_provider == "deepseek"
    assert settings.model_name == "deepseek-v4-flash"
    assert settings.provider_api_key == "key"
    assert settings.provider_base_url == "https://api.deepseek.com"


def test_openai_provider_uses_openai_key_and_default_model():
    settings = Settings(
        llm_provider="openai",
        openai_api_key="key",
        cml_url="https://cml.example",
        cml_username="user",
        cml_password="pass",
    )

    assert settings.model_name == "gpt-4.1-mini"
    assert settings.provider_api_key == "key"
    assert settings.provider_base_url is None
