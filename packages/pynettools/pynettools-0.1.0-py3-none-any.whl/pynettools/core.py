"""Core network utility functions."""

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def get(url: str, **kwargs):
    """GET request."""
    if not HAS_REQUESTS:
        raise ImportError("requests library required. Install with: pip install requests")
    return requests.get(url, **kwargs)


def post(url: str, **kwargs):
    """POST request."""
    if not HAS_REQUESTS:
        raise ImportError("requests library required. Install with: pip install requests")
    return requests.post(url, **kwargs)


def request(method: str, url: str, **kwargs):
    """Generic request."""
    if not HAS_REQUESTS:
        raise ImportError("requests library required. Install with: pip install requests")
    return requests.request(method, url, **kwargs)
