"""
API package for Market Data Orchestrator.

Provides:
- Control endpoints (pause/resume/reload)
- WebSocket status feed
- Authentication utilities
- Bundle orchestration (Phase 6)
"""

__version__ = "0.2.0"

from . import auth, control, websocket, federation, bundles

__all__ = ["auth", "control", "websocket", "federation", "bundles"]

