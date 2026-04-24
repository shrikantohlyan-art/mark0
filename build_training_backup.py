from __future__ import annotations

import time
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
TRAINING_DIR = ROOT_DIR / "Core" / "memory"
LOGS_DIR = ROOT_DIR / "logs"
OUTPUT_ZIP = ROOT_DIR / "Trained_Brain_Data.zip"

# Compression settings
COMPRESSION_LEVEL = 6  # Balance between compression and speed (1-9)
PROGRESS_INTERVAL = 10  # Show progress every N files


def _write_tree(archive: zipfile.ZipFile, tree_root: Path, base_root: Path, skipped: list[dict], progress_callback=None) -> int:
    """Write files from tree_root to archive with optional progress tracking."""
    count = 0
    if not tree_root.exists():
        return count

    for path in tree_root.rglob("*"):
        if path.is_dir():
            continue
        archive_name = path.relative_to(base_root).as_posix()
        try:
            with path.open("rb") as handle:
                archive.writestr(archive_name, handle.read(), compress_type=zipfile.ZIP_DEFLATED)
            count += 1
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(count, path.name)
                
        except Exception as exc:
            skipped.append({"path": str(path), "error": str(exc)})
    return count


def build_training_backup(root_dir: Path = ROOT_DIR, output_zip: Path = OUTPUT_ZIP) -> tuple[Path, list[dict], int]:
    """
    Build training backup with progress tracking.
    
    Args:
        root_dir: Root directory for relative paths
        output_zip: Output ZIP file path
        
    Returns:
        Tuple of (output_path, skipped_files_list, files_written_count)
    """
    root_dir = Path(root_dir).resolve()
    output_zip = Path(output_zip).resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    skipped: list[dict] = []

    training_dir = root_dir / "Core" / "memory"
    logs_dir = root_dir / "logs"
    training_dir.mkdir(parents=True, exist_ok=True)
    training_rules = training_dir / "training_rules.json"
    if not training_rules.exists():
        training_rules.write_text("[]\n", encoding="utf-8")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Count total files for progress reporting
    total_files = sum(1 for _ in training_dir.rglob("*") if _.is_file()) + \
                  sum(1 for _ in logs_dir.rglob("*") if _.is_file())
    
    print(f"📦 Starting backup: {total_files} files to archive...")
    print(f"   Target: {output_zip}")
    print(f"   Compression: level {COMPRESSION_LEVEL}/9")
    print()
    
    start_time = time.time()
    written_count = 0
    last_reported = 0
    
    def progress_callback(count: int, filename: str):
        nonlocal last_reported
        if count % PROGRESS_INTERVAL == 0 or count == total_files:
            percentage = (count / total_files * 100) if total_files > 0 else 0
            elapsed = time.time() - start_time
            rate = count / elapsed if elapsed > 0 else 0
            eta_seconds = (total_files - count) / rate if rate > 0 else 0
            
            print(f"  [{count:5}/{total_files:5}] {percentage:5.1f}% - {filename[:40]:40} "
                  f"({rate:5.1f} files/sec, ETA: {eta_seconds:6.1f}s)")
            last_reported = count

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=COMPRESSION_LEVEL) as archive:
        written_count += _write_tree(archive, training_dir, root_dir, skipped, progress_callback)
        written_count += _write_tree(archive, logs_dir, root_dir, skipped, progress_callback)

    elapsed = time.time() - start_time
    size_mb = output_zip.stat().st_size / (1024 * 1024)
    
    print()
    print(f"✅ Backup complete in {elapsed:.2f}s")
    print(f"   Files archived: {written_count}")
    print(f"   Output size: {size_mb:.2f} MB")
    if skipped:
        print(f"   Files skipped: {len(skipped)}")
    
    return output_zip, skipped, written_count


def main() -> int:
    """Main backup execution."""
    try:
        output_zip, skipped, written_count = build_training_backup()
        
        if skipped:
            print("\n⚠️  Skipped locked/unreadable files:")
            for item in skipped:
                print(f"   - {item['path']}: {item['error']}")
        
        return 0
    except Exception as e:
        print(f"\n❌ Backup failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
