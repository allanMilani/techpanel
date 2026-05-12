import pytest

from src.application.utils.github_remote import parse_github_owner_repo_from_remote_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("git@github.com:acme/app.git", "acme/app"),
        ("git@github.com:acme/app", "acme/app"),
        ("https://github.com/acme/app.git", "acme/app"),
        ("https://github.com/acme/app", "acme/app"),
        ("ssh://git@github.com/acme/app.git", "acme/app"),
        ("https://www.github.com/acme/app/", "acme/app"),
        ("", None),
        ("https://gitlab.com/a/b.git", None),
    ],
)
def test_parse_github_owner_repo_from_remote_url(raw: str, expected: str | None) -> None:
    assert parse_github_owner_repo_from_remote_url(raw) == expected
