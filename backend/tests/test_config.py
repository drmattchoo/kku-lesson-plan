from app.config import parse_csv_env


def test_parse_csv_env_splits_and_trims():
    assert parse_csv_env("a, b ,c") == ["a", "b", "c"]


def test_parse_csv_env_empty_string_returns_empty_list():
    assert parse_csv_env("") == []


def test_parse_csv_env_ignores_blank_entries():
    assert parse_csv_env("a,,  ,b") == ["a", "b"]


def test_parse_csv_env_preserves_wildcard():
    assert parse_csv_env("*") == ["*"]
