from pathlib import Path
from repo_review.ghpath import GHPath
from repo_review.testing import compute_check


def test_SI001_not_ok(tmp_path: Path):
    simple = tmp_path / "simple"
    simple.mkdir()

    simple.joinpath("LICENSE").write_text("Some other license")

    assert not compute_check("SI001", package=simple).result


def test_SI001_ok(tmp_path: Path):
    simple = tmp_path / "simple"
    simple.mkdir()

    simple.joinpath("LICENSE").write_text("MIT License")

    assert compute_check("SI001", package=simple).result


def test_SI002_not_ok(tmp_path: Path):
    simple = tmp_path / "simple"
    simple.mkdir()

    simple.joinpath("LICENSE").write_text("MIT License 2024 John Doe")

    assert not compute_check("SI002", package=simple).result


def test_SI002_ok(tmp_path: Path):
    simple = tmp_path / "simple"
    simple.mkdir()

    simple.joinpath("LICENSE").write_text("MIT License 2024 Simula Research Laboratory")

    assert compute_check("SI002", package=simple).result


def test_SI003_not_ok():
    package = GHPath(repo="someuser/somerepo", path="some/path", branch="main", _info=[{}])
    assert not compute_check("SI003", package=package).result


def test_SI003_ok():
    package = GHPath(
        repo="scientificcomputing/somerepo", path="some/path", branch="main", _info=[{}]
    )
    assert compute_check("SI003", package=package).result
