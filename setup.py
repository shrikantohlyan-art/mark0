#!/usr/bin/env python3
"""
Setup and installation script for JARVIS AI Assistant

Handles:
- Dependency installation (pip)
- Virtual environment setup verification
- Configuration initialization
- Database/cache setup
- System requirements verification
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_info(msg: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


def print_warning(msg: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_error(msg: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_header(title: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def check_python_version() -> bool:
    """Check if Python version is supported."""
    print_header("Python Version Check")
    
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    print(f"Python {current_version[0]}.{current_version[1]} detected")
    
    if current_version >= required_version:
        print_success(f"Python {required_version[0]}.{required_version[1]}+ supported")
        return True
    else:
        print_error(f"Python {required_version[0]}.{required_version[1]}+ required")
        return False


def install_requirements(upgrade: bool = False) -> bool:
    """Install Python dependencies."""
    print_header("Installing Python Dependencies")
    
    root_dir = Path(__file__).parent
    requirements_file = root_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print_error(f"Requirements file not found: {requirements_file}")
        return False
    
    print_info(f"Installing from: {requirements_file}")
    
    cmd = [sys.executable, "-m", "pip", "install"]
    
    if upgrade:
        cmd.append("--upgrade")
    
    cmd.extend(["-r", str(requirements_file)])
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print_success("Dependencies installed successfully")
            return True
        else:
            print_error(f"Dependency installation failed (exit code: {result.returncode})")
            return False
    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def setup_directories() -> bool:
    """Create required directories."""
    print_header("Setting Up Directories")
    
    root_dir = Path(__file__).parent
    required_dirs = [
        "logs/runtime",
        "config",
        "Cache",
        "Core/memory",
        "UserData",
        "Brain_Logs",
    ]
    
    try:
        for dir_name in required_dirs:
            dir_path = root_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"Directory ready: {dir_name}/")
        
        return True
    except Exception as e:
        print_error(f"Failed to create directories: {e}")
        return False


def init_config() -> bool:
    """Initialize configuration."""
    print_header("Initializing Configuration")
    
    try:
        from config_manager import ConfigManager
        
        # Create config manager and default configuration
        config = ConfigManager()
        
        # Validate configuration
        if config.validate():
            print_success("Configuration initialized and validated")
            return True
        else:
            print_warning("Configuration created but validation failed")
            return False
            
    except ImportError:
        print_warning("config_manager not available, skipping config initialization")
        return True
    except Exception as e:
        print_error(f"Failed to initialize configuration: {e}")
        return False


def verify_system_requirements() -> bool:
    """Verify system requirements."""
    print_header("Verifying System Requirements")
    
    checks = {
        "git": ["git", "--version"],
        "npm": ["npm", "--version"],
        "node": ["node", "--version"],
    }
    
    available = []
    missing = []
    
    for tool, cmd in checks.items():
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5, check=False)
            if result.returncode == 0:
                available.append(tool)
            else:
                missing.append(tool)
        except Exception:
            missing.append(tool)
    
    for tool in available:
        print_success(f"{tool} is installed")
    
    for tool in missing:
        print_warning(f"{tool} not found (optional)")
    
    return True


def main():
    """Main setup execution."""
    parser = argparse.ArgumentParser(description="JARVIS Setup and Installation")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade all packages")
    parser.add_argument("--skip-config", action="store_true", help="Skip configuration setup")
    parser.add_argument("--skip-verify", action="store_true", help="Skip system verification")
    
    args = parser.parse_args()
    
    print(f"""
{Colors.BOLD}{Colors.BLUE}
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║                  🚀 JARVIS Setup and Installation                  ║
║                                                                    ║
║  This script will:                                                 ║
║  ✓ Verify Python version                                           ║
║  ✓ Install dependencies                                            ║
║  ✓ Create required directories                                     ║
║  ✓ Initialize configuration                                        ║
║  ✓ Verify system requirements                                      ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
{Colors.END}
""")
    
    success = True
    
    # Step 1: Python version check
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Install requirements
    if not install_requirements(upgrade=args.upgrade):
        print_error("Failed to install dependencies")
        success = False
    
    # Step 3: Setup directories
    if not setup_directories():
        print_error("Failed to create directories")
        success = False
    
    # Step 4: Initialize configuration
    if not args.skip_config:
        if not init_config():
            print_warning("Configuration initialization incomplete")
    
    # Step 5: Verify system requirements
    if not args.skip_verify:
        verify_system_requirements()
    
    # Final summary
    print_header("Setup Summary")
    if success:
        print_success(f"Setup completed successfully!")
        print_info("Next steps:")
        print(f"  1. Review configuration: {Colors.BOLD}config/settings.json{Colors.END}")
        print(f"  2. Set API keys in: {Colors.BOLD}config/api_keys.json{Colors.END}")
        print(f"  3. Start backend: {Colors.BOLD}python -m Core.main{Colors.END}")
        print(f"  4. Start frontend: {Colors.BOLD}cd Interface/web && npm run dev{Colors.END}")
    else:
        print_error("Setup completed with errors - please review above")
        sys.exit(1)


if __name__ == "__main__":
    main()

