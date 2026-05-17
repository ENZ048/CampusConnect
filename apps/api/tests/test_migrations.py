import shutil
import subprocess
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]

# Locate `uv` - it may not be on PATH when tests run under pytest's subprocess.
_UV = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_UV, "run", "alembic", *args],
        cwd=API_DIR,
        capture_output=True,
        text=True,
    )


def test_alembic_upgrade_head_succeeds():
    result = _alembic("upgrade", "head")
    assert result.returncode == 0, result.stderr


def test_alembic_downgrade_base_then_upgrade_head_idempotent():
    for cmd in ("downgrade base", "upgrade head"):
        parts = cmd.split()
        result = _alembic(*parts)
        assert result.returncode == 0, f"{parts} failed: {result.stderr}"
