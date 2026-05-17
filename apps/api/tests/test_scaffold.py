from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_required_top_level_files_exist():
    for name in ["README.md", ".env.example", "Makefile", ".gitignore"]:
        assert (REPO_ROOT / name).is_file(), f"missing {name}"


def test_required_top_level_dirs_exist():
    for name in ["apps", "packages", "infra", "docs"]:
        assert (REPO_ROOT / name).is_dir(), f"missing {name}/"
