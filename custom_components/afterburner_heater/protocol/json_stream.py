"""JSON stream parser for fragmented BLE payloads.

This module handles incremental JSON parsing for BLE transports where
payloads may arrive in fragments across multiple notifications.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Max buffer size before forcing recovery
_MAX_BUFFER_SIZE = 2000
# Max chars to scan without finding a complete object before attempting recovery
_STALL_THRESHOLD = 500


class JsonObjectStream:
    """Incremental JSON object stream parser with corruption recovery."""

    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, text: str) -> list[dict[str, Any]]:
        """Feed a chunk of text and return decoded JSON objects."""
        if not text:
            return []

        self._buffer += text
        objects: list[dict[str, Any]] = []

        # Try to extract complete JSON objects
        while True:
            obj, remainder = self._try_extract_object()
            if obj is not None:
                objects.append(obj)
                self._buffer = remainder
            else:
                break

        # Buffer management - prevent unbounded growth
        if len(self._buffer) > _MAX_BUFFER_SIZE:
            self._attempt_recovery()

        return objects

    def _try_extract_object(self) -> tuple[dict[str, Any] | None, str]:
        """Try to extract a complete JSON object from the buffer.

        Returns (object, remainder) if successful, (None, buffer) if not.
        """
        # Find the first '{'
        start = self._buffer.find("{")
        if start == -1:
            # No object start found, clear non-JSON prefix
            return None, ""

        # Trim any garbage before the first '{'
        if start > 0:
            self._buffer = self._buffer[start:]
            start = 0

        # Try to find matching '}' using brace counting
        depth = 0
        in_string = False
        escape = False

        for i, char in enumerate(self._buffer):
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        # Found complete object boundary
                        candidate = self._buffer[: i + 1]
                        remainder = self._buffer[i + 1 :]
                        decoded = _try_decode(candidate)
                        if decoded is not None:
                            return decoded, remainder
                        else:
                            # JSON was malformed - skip this '{' and try next
                            _LOGGER.debug(
                                "Malformed JSON, skipping: %s...", candidate[:100]
                            )
                            self._buffer = self._buffer[1:]
                            return None, self._buffer

        # No complete object yet
        return None, self._buffer

    def _attempt_recovery(self) -> None:
        """Attempt to recover from buffer overflow/corruption."""
        _LOGGER.debug(
            "Buffer overflow (%d chars), attempting recovery", len(self._buffer)
        )

        # Strategy 1: Look for }{ boundary (back-to-back objects)
        match = re.search(r"\}\s*\{", self._buffer)
        if match:
            # Keep from the second '{' onwards
            recovery_point = match.end() - 1
            _LOGGER.debug("Recovery: found }{ at %d", recovery_point)
            self._buffer = self._buffer[recovery_point:]
            return

        # Strategy 2: Find the last '{' that might start a new object
        last_brace = self._buffer.rfind("{")
        if last_brace > 0 and last_brace > len(self._buffer) - 500:
            _LOGGER.debug("Recovery: keeping from last '{' at %d", last_brace)
            self._buffer = self._buffer[last_brace:]
            return

        # Strategy 3: Keep only the tail for potential partial object
        if len(self._buffer) > 200:
            _LOGGER.debug("Recovery: keeping last 200 chars")
            self._buffer = self._buffer[-200:]
            return

        # Last resort: clear everything
        _LOGGER.debug("Recovery: clearing buffer")
        self._buffer = ""

    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer = ""

    @property
    def buffer_size(self) -> int:
        """Return current buffer size."""
        return len(self._buffer)


def _try_decode(raw: str) -> dict[str, Any] | None:
    """Try to decode a JSON string, returning None on failure."""
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(decoded, dict):
        return decoded
    return None
