from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_ARCHIVE = ROOT_DIR / "Trained_Brain_Data.zip"
DEFAULT_FILEIO_URL = "https://www.file.io"


def load_environment() -> None:
    if callable(load_dotenv):
        load_dotenv(ROOT_DIR / ".env")


def _resolve_archive(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg).expanduser().resolve()
    return DEFAULT_ARCHIVE


def upload_to_discord_webhook(archive_path: Path, webhook_url: str) -> str:
    with archive_path.open("rb") as handle:
        response = requests.post(
            webhook_url,
            data={"content": f"Jarvis training backup: {archive_path.name}"},
            files={"file": (archive_path.name, handle, "application/zip")},
            timeout=180,
        )
    response.raise_for_status()
    payload = response.json()
    attachments = payload.get("attachments") or []
    if attachments and attachments[0].get("url"):
        return str(attachments[0]["url"])
    raise RuntimeError(
        "Discord webhook upload succeeded but no attachment URL was returned."
    )


def upload_to_fileio(archive_path: Path, upload_url: str = DEFAULT_FILEIO_URL) -> str:
    with archive_path.open("rb") as handle:
        response = requests.post(
            upload_url,
            files={"file": (archive_path.name, handle, "application/zip")},
            timeout=180,
        )
    response.raise_for_status()
    payload = response.json()
    link = payload.get("link") or payload.get("url")
    if not link:
        raise RuntimeError(
            f"file.io upload did not return a download link: {json.dumps(payload)}"
        )
    return str(link)


def transmit_archive(archive_path: Path) -> str:
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    load_environment()
    webhook_url = str(os.getenv("DISCORD_WEBHOOK_URL", "")).strip()
    fileio_url = (
        str(os.getenv("TRAINING_UPLOAD_URL", DEFAULT_FILEIO_URL)).strip()
        or DEFAULT_FILEIO_URL
    )

    if webhook_url:
        try:
            return upload_to_discord_webhook(archive_path, webhook_url)
        except Exception as exc:
            print(f"[WARN] Discord upload failed: {exc}")
            return upload_to_fileio(archive_path, fileio_url)
    return upload_to_fileio(archive_path, fileio_url)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload Jarvis training backup data.")
    parser.add_argument(
        "archive", nargs="?", help="Path to the training archive zip file."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate inputs without uploading."
    )
    args = parser.parse_args()

    archive_path = _resolve_archive(args.archive)
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    if args.dry_run:
        print(f"Dry run: archive ready at {archive_path}")
        return 0

    link = transmit_archive(archive_path)
    print(f"Secure Download Link: {link}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

