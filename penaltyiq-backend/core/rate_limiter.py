"""
Rate Limiter Singleton — PenaltyIQ Backend
===========================================
Single slowapi Limiter instance shared across all route files.
Import this module in both main.py (to bind to app.state) and
in any route file that decorates with @limiter.limit().
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
