from types import SimpleNamespace
from unittest.mock import MagicMock

from app.llm import LLMProvider, get_provider


def _fake_response(content: str):
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def test_complete_returns_message_content():
    provider = LLMProvider(model="claude-sonnet-4.6")
    provider.client.chat.completions.create = MagicMock(return_value=_fake_response("pong"))

    result = provider.complete("system prompt", "user prompt")

    assert result == "pong"
    provider.client.chat.completions.create.assert_called_once()
    _, kwargs = provider.client.chat.completions.create.call_args
    assert kwargs["model"] == "claude-sonnet-4.6"
    assert kwargs["messages"][0] == {"role": "system", "content": "system prompt"}
    assert kwargs["messages"][1] == {"role": "user", "content": "user prompt"}


def test_complete_json_parses_plain_json():
    provider = LLMProvider(model="gpt-5.5")
    provider.client.chat.completions.create = MagicMock(
        return_value=_fake_response('{"courseCode": "MD301"}')
    )

    result = provider.complete_json("system", "user")

    assert result == {"courseCode": "MD301"}


def test_complete_json_strips_markdown_fence():
    provider = LLMProvider(model="gpt-5.5")
    fenced = '```json\n{"courseCode": "MD301"}\n```'
    provider.client.chat.completions.create = MagicMock(return_value=_fake_response(fenced))

    result = provider.complete_json("system", "user")

    assert result == {"courseCode": "MD301"}


def test_get_provider_uses_configured_default_model(monkeypatch):
    import app.llm as llm_module

    monkeypatch.setattr(llm_module.settings, "llm_provider", "gpt")
    monkeypatch.setattr(llm_module.settings, "llm_model_gpt", "gpt-5.5")

    provider = get_provider()

    assert provider.model == "gpt-5.5"


def test_get_provider_allows_explicit_model_override():
    provider = get_provider(model="claude-sonnet-4.6")
    assert provider.model == "claude-sonnet-4.6"
