"""Utility functions for the DataScribe API.

This module provides utility functions for DataScribe API interactions.
"""

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def retry_session() -> Session:
    """Create a requests session with automatic retry logic for transient errors.

    The session will retry failed requests up to 5 times with exponential backoff (factor=4)
    for the following HTTP status codes: 429, 502, 503, 504, and for connection errors.
    Retries are handled using urllib3's Retry and requests' HTTPAdapter.

    Returns:
        Session: A requests session with retry logic enabled.
    """
    retry_strategy = Retry(
        total=5,
        backoff_factor=4,
        status_forcelist=[
            429,
            502,
            503,
            504,
        ],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
