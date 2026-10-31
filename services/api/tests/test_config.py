import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("https://a.vercel.app", ["https://a.vercel.app"]),
        (
            "https://a.vercel.app, http://localhost:3000",
            ["https://a.vercel.app", "http://localhost:3000"],
        ),
        ('["https://a.vercel.app"]', ["https://a.vercel.app"]),
        ("https://a.vercel.app/", ["https://a.vercel.app"]),
    ],
)
def test_cors_origins_parsing(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", raw)
    assert Settings(_env_file=None).cors_origins == expected
