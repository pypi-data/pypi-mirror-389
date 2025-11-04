

import pytest

from src import hentailib


def test_import():
    assert hentailib is not None

def test_version():
    import tomllib
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    version = data["project"]["version"]
    assert version == "1.0.0"