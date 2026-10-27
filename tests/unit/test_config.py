from pathlib import Path

import pytest

from kbqa.core.config import Settings, get_settings


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KBQA_WEAVIATE_URL", raising=False)
    monkeypatch.delenv("KBQA_ANTHROPIC_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.weaviate_url == "http://localhost:8080"
    assert settings.anthropic_api_key is None


def test_env_var_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KBQA_WEAVIATE_URL", "http://weaviate:9999")

    settings = Settings(_env_file=None)

    assert settings.weaviate_url == "http://weaviate:9999"


def test_api_key_is_not_leaked_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KBQA_ANTHROPIC_API_KEY", "sk-super-secret")

    settings = Settings(_env_file=None)

    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == "sk-super-secret"
    assert "sk-super-secret" not in repr(settings)
    assert "sk-super-secret" not in str(settings)


def test_reads_dotenv_file_from_working_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("KBQA_WEAVIATE_URL", raising=False)
    (tmp_path / ".env").write_text("KBQA_WEAVIATE_URL=http://from-dotenv:1234\n")
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    assert settings.weaviate_url == "http://from-dotenv:1234"


def test_env_var_beats_dotenv_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("KBQA_WEAVIATE_URL=http://from-dotenv:1234\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("KBQA_WEAVIATE_URL", "http://from-env:5678")

    settings = Settings()

    assert settings.weaviate_url == "http://from-env:5678"


def test_unknown_dotenv_keys_are_ignored(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("KBQA_NOT_A_SETTING=1\nSOMETHING_ELSE=2\n")
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    assert not hasattr(settings, "not_a_setting")


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("KBQA_WEAVIATE_URL", "http://first:1")

    first = get_settings()
    monkeypatch.setenv("KBQA_WEAVIATE_URL", "http://second:2")
    second = get_settings()
    get_settings.cache_clear()

    assert first is second
    assert second.weaviate_url == "http://first:1"
