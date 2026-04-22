from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app


def test_app_title() -> None:
    assert app.title == "TechPanel"
