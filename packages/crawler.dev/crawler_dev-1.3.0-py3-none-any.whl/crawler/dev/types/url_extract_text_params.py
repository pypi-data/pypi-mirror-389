# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, TypedDict

__all__ = ["URLExtractTextParams", "Proxy"]


class URLExtractTextParams(TypedDict, total=False):
    url: Required[str]
    """The URL to extract text from."""

    cache_age: int
    """Maximum cache time in milliseconds for the webpage.

    Must be between 0 (no caching) and 259200000 (3 days). Defaults to 172800000 (2
    days) if not specified.
    """

    clean_text: bool
    """Whether to clean extracted text"""

    headers: Dict[str, str]
    """Custom HTTP headers to send with the request (case-insensitive)"""

    max_redirects: int
    """Maximum number of redirects to follow when fetching the URL.

    Must be between 0 (no redirects) and 20. Defaults to 5 if not specified.
    """

    max_size: int
    """Maximum content length in bytes for the URL response.

    Must be between 1024 (1KB) and 52428800 (50MB). Defaults to 10485760 (10MB) if
    not specified.
    """

    max_timeout: int
    """Maximum time in milliseconds before the crawler gives up on loading a URL.

    Must be between 1000 (1 second) and 30000 (30 seconds). Defaults to 10000 (10
    seconds) if not specified.
    """

    proxy: Proxy
    """Proxy configuration for the request"""

    stealth_mode: bool
    """When enabled, we use a proxy for the request.

    If set to true, and the 'proxy' option is set, it will be ignored. Defaults to
    false if not specified. Note: Enabling stealth_mode consumes an additional
    credit/quota point (2 credits total instead of 1) for this request.
    """


class Proxy(TypedDict, total=False):
    password: str
    """Proxy password for authentication"""

    server: str
    """
    Proxy server URL (e.g., http://proxy.example.com:8080 or
    socks5://proxy.example.com:1080)
    """

    username: str
    """Proxy username for authentication"""
