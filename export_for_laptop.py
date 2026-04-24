from __future__ import annotations

import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_ZIP = ROOT_DIR / "Jarvis_Laptop_Deploy.zip"
IGNORE_DIRS = {".venv", "node_modules", "__pycache__", ".git"}
REQUIRED_ROOT_FILES = [
    ".env",
    "requirements.txt",
    "build_training_backup.py",
    "transmit_data.py",
]
REQUIRED_TREES = [
    "Core",
    "Interface/web",
]


def _should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def _iter_tree_files(root: Path, tree_name: str):
    tree_root = root / tree_name
    if not tree_root.exists():
        raise FileNotFoundError(f"Required path not found: {tree_root}")
    for path in tree_root.rglob("*"):
        if path.is_dir():
            continue
        if _should_skip(path.relative_to(root)):
            continue
        yield path


def _iter_root_batch_files(root: Path):
    for path in sorted(root.glob("*.bat")):
        if path.is_file():
            yield path


def build_deploy_zip(root_dir: Path = ROOT_DIR, output_zip: Path = OUTPUT_ZIP) -> Path:
    root_dir = Path(root_dir).resolve()
    output_zip = Path(output_zip).resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative_name in REQUIRED_ROOT_FILES:
            source = root_dir / relative_name
            if not source.exists():
                raise FileNotFoundError(f"Required file not found: {source}")
            archive.write(source, source.relative_to(root_dir).as_posix())

        for source in _iter_root_batch_files(root_dir):
            archive.write(source, source.relative_to(root_dir).as_posix())

        for tree_name in REQUIRED_TREES:
            for source in _iter_tree_files(root_dir, tree_name):
                archive.write(source, source.relative_to(root_dir).as_posix())

    return output_zip


def main() -> int:
    archive_path = build_deploy_zip()
    print(f"Laptop deploy archive created: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
