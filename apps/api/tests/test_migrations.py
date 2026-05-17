import subprocess
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_head_succeeds():
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=API_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_alembic_downgrade_base_then_upgrade_head_idempotent():
    for cmd in (["downgrade", "base"], ["upgrade", "head"]):
        result = subprocess.run(
            ["uv", "run", "alembic", *cmd],
            cwd=API_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{cmd} failed: {result.stderr}"
