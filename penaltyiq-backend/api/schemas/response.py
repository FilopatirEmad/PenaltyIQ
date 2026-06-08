"""
Standard API Response Schemas — PenaltyIQ Backend
===================================================
All endpoints return one of two shapes:

  SUCCESS:
    {"success": true, "data": <payload>, "message": ""}

  ERROR:
    {"success": false, "error": "<message>", "data": null}

Helper functions `ok()` and `err()` are used in route handlers.
"""

from typing import Any, Optional


def ok(data: Any, message: str = "") -> dict:
    """Return a standardised success response."""
    return {
        "success": True,
        "data": data,
        "message": message,
    }


def err(error: str) -> dict:
    """Return a standardised error response."""
    return {
        "success": False,
        "error": error,
        "data": None,
    }
