"""
SDK Constants - SDK Layer Configuration Constants

Contains heartbeat intervals and other configuration constants.
These constants can be used by both SDK and Application layers.

This ensures SDK independence - application layer can import from SDK,
but SDK should NEVER import from application layer.
"""

# Heartbeat Configuration
# Used by WebSocket connection monitoring and self-healing mechanisms

HEARTBEAT_INTERVAL = 30  # seconds - interval for updating heartbeat
HEARTBEAT_TIMEOUT = 60  # seconds - if no heartbeat for this long, consider connection dead
HEARTBEAT_MONITOR_INTERVAL = 30  # seconds - interval for checking heartbeat health


__all__ = [
    'HEARTBEAT_INTERVAL',
    'HEARTBEAT_TIMEOUT',
    'HEARTBEAT_MONITOR_INTERVAL',
]
