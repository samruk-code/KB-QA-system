import pytest

from kbqa.core.config import Settings


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
