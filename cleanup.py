#!/usr/bin/env python3
"""
🧹 JARVIS PHASE 0.5 CLEANUP SCRIPT
Final project organization and duplicate removal.

Usage: 
    python cleanup.py              # Interactive mode
    python cleanup.py --dry-run    # Show what would be done without making changes
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Global dry-run flag
DRY_RUN = False

# ============================================================================
# CONFIGURATION
# ============================================================================

# Root directory (where this script runs from)
ROOT_DIR = Path(__file__).parent.absolute()

# Target directories
DOCS_DIR = ROOT_DIR / "Docs"
ARCHIVE_DIR = ROOT_DIR / "Archive"
BRAIN_LOGS_DIR = ROOT_DIR / "Brain_Logs"
CORE_DIR = ROOT_DIR / "Core"

# Files to NEVER move or delete
PROTECTED_FILES = {".env", "README.md", "Jarvis_Launcher.vbs", "DIRECT_LAUNCH.bat", "cleanup.py"}

# Only keep these in root after cleanup
ALLOWED_ROOT_ITEMS = {
    "Core", "Interface", "Brain_Logs", "UserData", "Docs", "Archive",
    ".env", "README.md", "Jarvis_Launcher.vbs", "DIRECT_LAUNCH.bat",
    "launch_jarvis.pyw", "launcher_bootstrap.py", "setup.py"
}

# Folders to archive (move to /Archive)
FOLDERS_TO_ARCHIVE = {
    "jarvis-1", "jarvis-ui-redesign", "jarvis-ui-redesign-backup",
    "training_logs", "jarvis", "__pycache__", ".git"
}

# Files to check for duplicates in root (delete if exist in Core)
DUPLICATE_FILES = {"main.py", "agent.py", "tools.py", "router.py"}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

class Colors:
    """Terminal colors for output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{title:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}\n")

def print_success(msg):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_info(msg):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ {msg}{Colors.END}")

def print_warning(msg):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_error(msg):
    """Print error message."""
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def safe_move(src, dst, file_type="file"):
    """Safely move file or folder (respects DRY_RUN mode)."""
    try:
        if not src.exists():
            print_warning(f"{file_type} not found: {src.name}")
            return False
        
        if dst.exists():
            print_warning(f"Destination exists, overwriting: {dst.name}")
        
        # Ensure parent directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        if DRY_RUN:
            action = "Would move" if not DRY_RUN else "Would move (DRY-RUN)"
            print(f"{Colors.CYAN}{action}: {src.name} → {dst.name}{Colors.END}")
            return True
        
        if src.is_dir():
            shutil.move(str(src), str(dst))
        else:
            shutil.move(str(src), str(dst))
        
        print_success(f"Moved: {src.name} → {dst.name}")
        return True
    except Exception as e:
        print_error(f"Failed to move {src.name}: {e}")
        return False

def safe_delete(src, file_type="file"):
    """Safely delete file or folder (respects DRY_RUN mode)."""
    try:
        if not src.exists():
            print_warning(f"{file_type} not found: {src.name}")
            return False
        
        if DRY_RUN:
            print(f"{Colors.CYAN}Would delete (DRY-RUN): {src.name}{Colors.END}")
            return True
        
        if src.is_dir():
            shutil.rmtree(src)
        else:
            src.unlink()
        
        print_success(f"Deleted: {src.name}")
        return True
    except Exception as e:
        print_error(f"Failed to delete {src.name}: {e}")
        return False

def count_files(directory, extension=None):
    """Count files in directory."""
    if not directory.exists():
        return 0
    if extension:
        return len(list(directory.glob(f"*{extension}")))
    return len(list(directory.rglob("*")))

# ============================================================================
# CLEANUP OPERATIONS
# ============================================================================

def create_essential_folders():
    """Create essential folders if they don't exist."""
    print_header("📂 STEP 1: Creating Essential Folders")
    
    folders = [DOCS_DIR, ARCHIVE_DIR, BRAIN_LOGS_DIR]
    for folder in folders:
        if folder.exists():
            print_info(f"Already exists: {folder.name}/")
        else:
            folder.mkdir(parents=True, exist_ok=True)
            print_success(f"Created: {folder.name}/")

def cleanup_documentation():
    """Move documentation files to /Docs."""
    print_header("📚 STEP 2: Documentation Hub")
    print_info("Moving .md, .txt, and .pdf files to /Docs")
    print_info("Protected: README.md, .env (will not be moved)")
    
    moved_count = 0
    
    # Find all documentation files in root
    for pattern in ["*.md", "*.txt", "*.pdf"]:
        for file in sorted(ROOT_DIR.glob(pattern)):
            # Skip protected files
            if file.name in PROTECTED_FILES:
                print_warning(f"Protected: {file.name} (skipped)")
                continue
            
            # Skip hidden/system files
            if file.name.startswith("."):
                continue
            
            dst = DOCS_DIR / file.name
            if safe_move(file, dst, "file"):
                moved_count += 1
    
    print_info(f"Total documentation files moved: {moved_count}")

def cleanup_duplicates():
    """Delete duplicate files from root if they exist in /Core."""
    print_header("🔄 STEP 3: Duplicate Liquidation")
    print_info("Checking for duplicates in /Core folder")
    
    deleted_count = 0
    
    # Check if /Core has the master files
    core_files = set(f.name for f in CORE_DIR.glob("*.py")) if CORE_DIR.exists() else set()
    
    if not core_files:
        print_warning("Core folder empty or not found. Skipping duplicate cleanup.")
        return
    
    print_info(f"Found {len(core_files)} Python files in /Core")
    
    # Delete duplicates from root
    for dup_file in DUPLICATE_FILES:
        root_file = ROOT_DIR / dup_file
        core_file = CORE_DIR / dup_file
        
        if root_file.exists() and core_file.exists():
            print_info(f"Duplicate found: {dup_file}")
            print_info(f"  - Root: {root_file}")
            print_info(f"  - Core: {core_file} (KEEPING)")
            if safe_delete(root_file, "file"):
                deleted_count += 1
        elif root_file.exists() and not core_file.exists():
            print_warning(f"Only in root: {dup_file} (keeping as no Core version)")
        else:
            print_info(f"Not found in root: {dup_file}")
    
    print_info(f"Total duplicate files deleted: {deleted_count}")

def cleanup_logs():
    """Move log files and memory.txt to /Brain_Logs."""
    print_header("📝 STEP 4: Log Management")
    print_info("Moving logs and memory files to /Brain_Logs")
    
    moved_count = 0
    
    # Create Brain_Logs if not exists
    BRAIN_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Move .log files
    for log_file in sorted(ROOT_DIR.glob("*.log")):
        if log_file.name.startswith("."):
            continue
        dst = BRAIN_LOGS_DIR / log_file.name
        if safe_move(log_file, dst, "file"):
            moved_count += 1
    
    # Move memory.txt
    memory_file = ROOT_DIR / "memory.txt"
    if memory_file.exists():
        dst = BRAIN_LOGS_DIR / "memory.txt"
        if safe_move(memory_file, dst, "file"):
            moved_count += 1
    
    print_info(f"Total log files moved: {moved_count}")

def archive_old_versions():
    """Move backup folders to /Archive."""
    print_header("📦 STEP 5: Archive Old Versions")
    print_info("Moving backup folders to /Archive")
    print_info(f"Looking for: {', '.join(sorted(FOLDERS_TO_ARCHIVE))}")
    
    moved_count = 0
    
    for folder_name in sorted(FOLDERS_TO_ARCHIVE):
        folder_path = ROOT_DIR / folder_name
        
        if folder_path.exists():
            dst = ARCHIVE_DIR / folder_name
            if safe_move(folder_path, dst, "folder"):
                moved_count += 1
    
    print_info(f"Total folders archived: {moved_count}")

def verify_core_structure():
    """Verify that /Core has required files."""
    print_header("🔍 STEP 6: Verifying Core Structure")
    
    required_in_core = DUPLICATE_FILES.copy()
    
    if not CORE_DIR.exists():
        print_error("Core folder does not exist!")
        return False
    
    missing_files = []
    for file in required_in_core:
        file_path = CORE_DIR / file
        if file_path.exists():
            print_success(f"✓ {file} exists in /Core")
        else:
            print_warning(f"✗ {file} NOT found in /Core")
            missing_files.append(file)
    
    if missing_files:
        print_warning(f"Missing in /Core: {', '.join(missing_files)}")
        return False
    
    print_success("All required files present in /Core")
    return True

def cleanup_root_directory():
    """Remove unwanted files from root."""
    print_header("🧹 STEP 7: Root Integrity Check")
    print_info("Checking for unwanted files/folders in root")
    
    to_delete = []
    
    for item in sorted(ROOT_DIR.iterdir()):
        # Skip protected and allowed items
        if item.name in PROTECTED_FILES or item.name in ALLOWED_ROOT_ITEMS:
            continue
        
        # Skip hidden files
        if item.name.startswith("."):
            continue
        
        # Skip __pycache__
        if item.name == "__pycache__":
            continue
        
        # Collect items to delete
        if item.is_dir() or (item.is_file() and item.suffix in {".py", ".md", ".txt", ".log"}):
            # Already moved or protected? Check one more time
            if item.name not in {"main.py", "agent.py", "tools.py", "router.py"}:
                # Some files might have been marked for deletion
                pass

def display_final_structure():
    """Display final directory structure."""
    print_header("📊 FINAL DIRECTORY STRUCTURE")
    
    print(f"{Colors.BOLD}Root Directory ({ROOT_DIR.name}/):{Colors.END}")
    print()
    
    allowed_items = sorted([
        "Core", "Interface", "Brain_Logs", "UserData", "Docs", "Archive",
        ".env", "README.md", "Jarvis_Launcher.vbs", "setup.py"
    ])
    
    for item_name in allowed_items:
        item_path = ROOT_DIR / item_name
        if item_path.exists():
            if item_path.is_dir():
                item_count = len(list(item_path.glob("*")))
                print(f"  {Colors.CYAN}📂{Colors.END} {item_name:30} ({item_count} items)")
            else:
                size_kb = item_path.stat().st_size / 1024
                print(f"  {Colors.CYAN}📄{Colors.END} {item_name:30} ({size_kb:.1f} KB)")
        else:
            print(f"  {Colors.YELLOW}○{Colors.END} {item_name:30} (not found)")
    
    print()
    print(f"{Colors.BOLD}Key Subdirectories:{Colors.END}")
    print()
    
    # Show Docs contents
    if DOCS_DIR.exists():
        doc_files = list(DOCS_DIR.glob("*.*"))
        print(f"  {Colors.GREEN}Docs/{Colors.END} ({len(doc_files)} files)")
        for doc in sorted(doc_files)[:5]:
            print(f"    ├─ {doc.name}")
        if len(doc_files) > 5:
            print(f"    └─ ... and {len(doc_files) - 5} more")
    
    print()
    
    # Show Archive contents
    if ARCHIVE_DIR.exists():
        arch_items = list(ARCHIVE_DIR.glob("*"))
        print(f"  {Colors.GREEN}Archive/{Colors.END} ({len(arch_items)} items)")
        for item in sorted(arch_items):
            print(f"    ├─ {item.name}/")
    
    print()
    
    # Show Brain_Logs contents
    if BRAIN_LOGS_DIR.exists():
        log_count = len(list(BRAIN_LOGS_DIR.glob("*")))
        print(f"  {Colors.GREEN}Brain_Logs/{Colors.END} ({log_count} items)")

def generate_cleanup_report():
    """Generate a summary report."""
    print_header("📋 CLEANUP REPORT")
    
    print(f"{Colors.BOLD}Status: {Colors.GREEN}✓ CLEANUP COMPLETE{Colors.END}\n")
    
    reports = [
        ("Documentation Hub", DOCS_DIR, "files"),
        ("Archive Folder", ARCHIVE_DIR, "backup folders"),
        ("Brain_Logs", BRAIN_LOGS_DIR, "log files"),
        ("Core Directory", CORE_DIR, "Python files"),
    ]
    
    for name, path, desc in reports:
        if path.exists():
            count = len(list(path.glob("*")))
            print(f"  {Colors.GREEN}✓{Colors.END} {name:25} - {count:3} {desc}")
        else:
            print(f"  {Colors.YELLOW}○{Colors.END} {name:25} - not found")
    
    print()
    print(f"{Colors.BOLD}Next Steps:{Colors.END}")
    print(f"  1. Review {Colors.CYAN}Docs/{Colors.END} folder for documentation")
    print(f"  2. Check {Colors.CYAN}Archive/{Colors.END} for backed-up files")
    print(f"  3. Verify {Colors.CYAN}Core/{Colors.END} has all required modules")
    print(f"  4. Start Jarvis with: {Colors.CYAN}python -m Core.main{Colors.END}")
    print()

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main cleanup execution."""
    global DRY_RUN
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="JARVIS Phase 0.5 cleanup script - organize project files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup.py              # Interactive cleanup
  python cleanup.py --dry-run    # Preview changes without executing
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes"
    )
    args = parser.parse_args()
    
    DRY_RUN = args.dry_run
    
    print(f"""
{Colors.BOLD}{Colors.BLUE}
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║           🧹 JARVIS PHASE 0.5 CLEANUP SCRIPT                       ║
║          Final Organization and Duplicate Removal                  ║
║                                                                    ║
║  This script will:                                                 ║
║  ✓ Create documentation hub                                        ║
║  ✓ Remove duplicate files                                          ║
║  ✓ Organize logs and memory files                                  ║
║  ✓ Archive old backup folders                                      ║
║  ✓ Verify project structure                                        ║
║                                                                    ║
{f"║  {Colors.YELLOW}DRY-RUN MODE: Changes will NOT be applied{Colors.BLUE}                     ║" if DRY_RUN else "║                                                                    ║"}
╚════════════════════════════════════════════════════════════════════╝
{Colors.END}""")
    
    if not DRY_RUN:
        print(f"\n{Colors.YELLOW}⚠️  WARNING: This script will move and delete files!{Colors.END}")
        print(f"{Colors.YELLOW}⚠️  Make sure you have a backup if needed.{Colors.END}\n")
        
        # Confirmation
        response = input(f"{Colors.BOLD}Continue with cleanup? (yes/no): {Colors.END}").strip().lower()
        if response not in {"yes", "y"}:
            print(f"{Colors.YELLOW}Cleanup cancelled.{Colors.END}")
            sys.exit(0)
    else:
        print(f"\n{Colors.CYAN}Running in DRY-RUN mode - no changes will be made{Colors.END}\n")
    
    print()
    
    try:
        # Execute cleanup steps
        create_essential_folders()
        cleanup_documentation()
        cleanup_duplicates()
        cleanup_logs()
        archive_old_versions()
        verify_core_structure()
        
        # Display results
        display_final_structure()
        generate_cleanup_report()
        
        if DRY_RUN:
            print(f"{Colors.CYAN}{Colors.BOLD}✓ DRY-RUN COMPLETE (no changes were made){Colors.END}\n")
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ CLEANUP SUCCESSFUL!{Colors.END}\n")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cleanup interrupted by user.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: Cleanup failed!{Colors.END}")
        print(f"{Colors.RED}{str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
