"""
System health check utilities for JARVIS
"""
import psutil
import sys
from pathlib import Path
from typing import Dict, Any
import socket
import logging

logger = logging.getLogger(__name__)


def get_system_health() -> Dict[str, Any]:
    """
    Comprehensive system health check.
    
    Returns:
        Dictionary containing system health metrics
    """
    try:
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory information
        memory = psutil.virtual_memory()
        
        # Disk information
        disk = psutil.disk_usage('/')
        
        # Network information
        try:
            net_connections = len(psutil.net_connections())
        except (psutil.AccessDenied, OSError):
            net_connections = 0
        
        # Process information
        process_count = len(psutil.pids())
        
        health = {
            "status": "healthy",
            "python_version": sys.version,
            "python_executable": sys.executable,
            "platform": sys.platform,
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "count_logical": psutil.cpu_count(logical=True)
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent": memory.percent,
                "used_gb": memory.used / (1024**3)
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": disk.percent
            },
            "processes": process_count,
            "network_connections": net_connections,
            "hostname": socket.gethostname()
        }
        
        # Check for issues
        if cpu_percent > 80:
            health["status"] = "warning"
            health["warnings"] = health.get("warnings", [])
            health["warnings"].append(f"High CPU usage: {cpu_percent}%")
        
        if memory.percent > 85:
            health["status"] = "warning"
            health["warnings"] = health.get("warnings", [])
            health["warnings"].append(f"High memory usage: {memory.percent}%")
        
        if disk.percent > 90:
            health["status"] = "warning"
            health["warnings"] = health.get("warnings", [])
            health["warnings"].append(f"High disk usage: {disk.percent}%")
        
        return health
    
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def check_required_ports(ports: list = None) -> Dict[str, bool]:
    """
    Check if required ports are available.
    
    Args:
        ports: List of ports to check (default: [8001, 5173])
    
    Returns:
        Dictionary mapping port to availability status
    """
    if ports is None:
        ports = [8001, 5173]  # Default: backend and frontend ports
    
    port_status = {}
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            port_status[port] = result != 0  # True if unavailable (connection refused)
        except Exception as e:
            logger.warning(f"Error checking port {port}: {e}")
            port_status[port] = False
    
    return port_status


def check_dependencies(dependencies: list = None) -> Dict[str, bool]:
    """
    Check if required Python dependencies are installed.
    
    Args:
        dependencies: List of module names to check
    
    Returns:
        Dictionary mapping dependency to availability status
    """
    if dependencies is None:
        dependencies = [
            "fastapi", "uvicorn", "pydantic", "requests",
            "google.genai", "edge_tts", "psutil"
        ]
    
    dep_status = {}
    
    for dep in dependencies:
        try:
            __import__(dep)
            dep_status[dep] = True
        except ImportError:
            dep_status[dep] = False
            logger.warning(f"Missing dependency: {dep}")
    
    return dep_status


def full_health_report() -> Dict[str, Any]:
    """
    Generate a comprehensive health report.
    
    Returns:
        Complete health report with all checks
    """
    return {
        "system": get_system_health(),
        "ports": check_required_ports(),
        "dependencies": check_dependencies()
    }
