"""Tests for the Codex config helper used by the Harbor Codex wrapper."""

from __future__ import annotations

import textwrap

import pytest

from medcli.agents.harbor.installed.codex import (
    collect_env_keys_from_config,
    resolve_codex_config,
)


@pytest.fixture
def dual_provider_config(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        textwrap.dedent(
            """
            model = "gpt-5.4"
            model_provider = "azure_eus"

            [model_providers.azure_wus3]
            name = "Azure OpenAI (West US 3)"
            base_url = "https://wus3.example.com/openai/v1"
            env_key = "AZURE_OPENAI_WUS3_API_KEY"
            wire_api = "responses"

            [model_providers.azure_eus]
            name = "Azure OpenAI (East US)"
            base_url = "https://eus.example.com/openai/v1"
            env_key = "AZURE_OPENAI_EUS_API_KEY"
            wire_api = "responses"

            [model_providers.no_env_key]
            name = "Provider without env_key"
            base_url = "https://noenv.example.com/openai/v1"
            wire_api = "responses"
            """
        ).strip()
    )
    return config


def test_collect_env_keys_returns_only_set_keys(dual_provider_config, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_WUS3_API_KEY", "wus3-secret")
    monkeypatch.delenv("AZURE_OPENAI_EUS_API_KEY", raising=False)

    resolved = collect_env_keys_from_config(dual_provider_config)

    assert resolved == {"AZURE_OPENAI_WUS3_API_KEY": "wus3-secret"}


def test_collect_env_keys_picks_up_both_when_set(dual_provider_config, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_WUS3_API_KEY", "wus3-secret")
    monkeypatch.setenv("AZURE_OPENAI_EUS_API_KEY", "eus-secret")

    resolved = collect_env_keys_from_config(dual_provider_config)

    assert resolved == {
        "AZURE_OPENAI_WUS3_API_KEY": "wus3-secret",
        "AZURE_OPENAI_EUS_API_KEY": "eus-secret",
    }


def test_collect_env_keys_skips_empty_values(dual_provider_config, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_WUS3_API_KEY", "   ")
    monkeypatch.delenv("AZURE_OPENAI_EUS_API_KEY", raising=False)

    assert collect_env_keys_from_config(dual_provider_config) == {}


def test_collect_env_keys_returns_empty_when_no_providers(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('model = "gpt-5.4"\n')

    assert collect_env_keys_from_config(config) == {}


def test_collect_env_keys_raises_on_malformed_toml(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text("model = \n")  # truncated value, invalid TOML

    with pytest.raises(ValueError, match="Failed to parse Codex config"):
        collect_env_keys_from_config(config)


def test_resolve_codex_config_honors_override(tmp_path, monkeypatch):
    config = tmp_path / "elsewhere.toml"
    config.write_text("")
    monkeypatch.setenv("CODEX_CONFIG_FILE", str(config))

    assert resolve_codex_config() == config


def test_resolve_codex_config_missing_raises(monkeypatch, tmp_path):
    missing = tmp_path / "does-not-exist.toml"
    monkeypatch.setenv("CODEX_CONFIG_FILE", str(missing))

    with pytest.raises(ValueError, match="Codex config file not found"):
        resolve_codex_config()
