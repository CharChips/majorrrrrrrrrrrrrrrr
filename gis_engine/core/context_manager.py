"""
Context manager for maintaining workflow state and data.
"""

import datetime


class ContextManager:
    """Manages workflow context and intermediate data."""

    def __init__(self):
        """Initialize the context manager."""
        self.data = {}
        self.logs = []
        self.current_step = None
        self.metadata = {}

    # --------------------------------------------------
    # Data Handling
    # --------------------------------------------------

    def set(self, key, value):
        """Store a value in context."""
        self.data[key] = value
        self._log(f"Stored key: {key}")

    def get(self, key, required=True):
        """
        Retrieve a value from context.

        Args:
            key: Key to retrieve.
            required: If True, raise error if missing.
        """
        if key not in self.data:
            if required:
                raise KeyError(f"Context key '{key}' not found.")
            return None
        return self.data[key]

    def exists(self, key):
        """Check if key exists."""
        return key in self.data

    def delete(self, key):
        """Remove key from context."""
        if key in self.data:
            del self.data[key]
            self._log(f"Deleted key: {key}")

    def clear(self):
        """Clear all context data."""
        self.data.clear()
        self.logs.clear()
        self.metadata.clear()
        self.current_step = None

    # --------------------------------------------------
    # Workflow Step Tracking
    # --------------------------------------------------

    def set_step(self, step_name):
        """Set current workflow step."""
        self.current_step = step_name
        self._log(f"Executing step: {step_name}")

    def get_current_step(self):
        """Get current workflow step."""
        return self.current_step

    # --------------------------------------------------
    # Logging System
    # --------------------------------------------------

    def _log(self, message):
        """Internal logging with timestamp."""
        timestamp = datetime.datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")

    def add_log(self, message):
        """Public logging method."""
        self._log(message)

    def get_logs(self):
        """Return all execution logs."""
        return self.logs

    # --------------------------------------------------
    # Metadata Storage
    # --------------------------------------------------

    def set_metadata(self, key, value):
        """Store metadata related to workflow."""
        self.metadata[key] = value

    def get_metadata(self, key):
        """Retrieve metadata."""
        return self.metadata.get(key)

    def get_all_metadata(self):
        """Return full metadata dictionary."""
        return self.metadata

    # --------------------------------------------------
    # Debug Snapshot
    # --------------------------------------------------

    def snapshot(self):
        """Return full context snapshot (for debugging or UI display)."""
        return {
            "data_keys": list(self.data.keys()),
            "current_step": self.current_step,
            "logs": self.logs,
            "metadata": self.metadata
        }