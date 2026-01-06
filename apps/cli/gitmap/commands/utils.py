"""Utility functions for GitMap CLI commands.

Execution Context:
    CLI command utilities - imported by command modules

Dependencies:
    - os: Environment variable access

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import os


def get_portal_url(url: str | None = None) -> str:
    """Get Portal URL from parameter or environment variable.
    
    Portal URL MUST be provided either as a parameter or via PORTAL_URL
    environment variable. No default fallback to arcgis.com is provided.
    
    Args:
        url: Optional Portal URL parameter (takes precedence if provided).
    
    Returns:
        Portal URL string.
    
    Raises:
        ValueError: If neither url parameter nor PORTAL_URL env var is set.
    """
    # If URL is explicitly provided, use it
    if url:
        return url
    
    # Otherwise, require PORTAL_URL environment variable
    portal_url = os.getenv("PORTAL_URL")
    if not portal_url:
        raise ValueError(
            "Portal URL is required. Set PORTAL_URL environment variable "
            "in your .env file or provide --url parameter."
        )
    
    return portal_url

