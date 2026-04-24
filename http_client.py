"""
Unified HTTP client with connection pooling and retry logic
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any
import logging
import threading

logger = logging.getLogger(__name__)


class HttpClient:
    """Singleton HTTP client with connection pooling."""
    
    _sessions: Dict[str, requests.Session] = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_session(cls, base_url: str = "default") -> requests.Session:
        """
        Get or create an HTTP session with connection pooling.
        
        Args:
            base_url: Identifier for the session (default: "default")
        
        Returns:
            Configured requests.Session with pooling and retries
        """
        with cls._lock:
            if base_url not in cls._sessions:
                cls._sessions[base_url] = cls._create_session()
            return cls._sessions[base_url]
    
    @staticmethod
    def _create_session(
        max_retries: int = 3,
        backoff_factor: float = 0.1,
        status_forcelist: list = None,
        pool_connections: int = 10,
        pool_maxsize: int = 10
    ) -> requests.Session:
        """
        Create a new HTTP session with retry strategy.
        
        Args:
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for exponential backoff
            status_forcelist: HTTP status codes to retry on
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum size of connection pool
        
        Returns:
            Configured requests.Session
        """
        if status_forcelist is None:
            status_forcelist = [429, 500, 502, 503, 504]
        
        session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    @classmethod
    def get(
        cls,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        quiet: bool = False,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> requests.Response:
        """Make a GET request with connection pooling."""
        if max_retries is not None:
            session = cls._create_session(max_retries=max_retries)
        else:
            session = cls.get_session()

        try:
            return session.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
        except Exception as e:
            if not quiet:
                logger.error(f"GET request failed to {url}: {e}")
            raise
    
    @classmethod
    def post(
        cls,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        quiet: bool = False,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> requests.Response:
        """Make a POST request with connection pooling."""
        if max_retries is not None:
            session = cls._create_session(max_retries=max_retries)
        else:
            session = cls.get_session()

        try:
            return session.post(url, data=data, json=json, headers=headers, timeout=timeout, **kwargs)
        except Exception as e:
            if not quiet:
                logger.error(f"POST request failed to {url}: {e}")
            raise
    
    @classmethod
    def close_all(cls):
        """Close all active sessions."""
        with cls._lock:
            try:
                for session in cls._sessions.values():
                    try:
                        session.close()
                    except Exception:
                        pass
                cls._sessions.clear()
            finally:
                logger.debug("All HTTP sessions closed")


def make_request(
    method: str,
    url: str,
    **kwargs
) -> requests.Response:
    """
    Convenience function for making HTTP requests.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        **kwargs: Additional arguments to pass to session method
    
    Returns:
        Response object
    """
    session = HttpClient.get_session()
    
    try:
        response = session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"{method} request to {url} failed: {e}")
        raise
