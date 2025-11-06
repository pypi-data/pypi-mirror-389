import asyncio
from dataclasses import dataclass, field
import threading
from typing import Any, Awaitable, Callable, Dict, Optional
import numpy as np

@dataclass
class ReactorContext:
    """
    Session-scoped context passed to the model.
    """
    _send_fn: Callable[[dict], None]
    _emit_block_fn: Callable[[Optional[np.ndarray]], None]
    _enable_monitoring_fn: Callable[[], None]
    _disable_monitoring_fn: Callable[[], None]
    _stop_evt: threading.Event = None

    def send(self, data: dict) -> None:
        """
        Send a payload from the model to the frontend.
        Runtime wraps this into an ApplicationMessage envelope before sending.
        """
        self._send_fn(data)

    def emit_block(self, frames: Optional[np.ndarray]) -> None:
        """
        Emits a frame or list of frames to the videostream, displaying them on the client feed.
        Frames should be a NumPy ndarray (H, W, 3) in RGB, or a stack of frames with the stack on the first dimension (N, H, W, 3).
        If None, the frame buffer will put the None through in the frame, allowing the video streamer to send a black frame.
        """
        self._emit_block_fn(frames)

    def enable_monitoring(self) -> None:
        """
        Enable frame monitoring mode for performance tracking.
        """
        self._enable_monitoring_fn()

    def disable_monitoring(self) -> None:
        """
        Disable frame monitoring mode for performance tracking.
        """
        self._disable_monitoring_fn()


ctx: Optional[ReactorContext] = None


def get_ctx() -> ReactorContext:
    """Get the current global context. Raises if not set."""
    if ctx is None:
        raise RuntimeError("Global context not set. This should only be called during an active session.")
    return ctx


def _set_global_ctx(context: ReactorContext):
    global ctx
    ctx = context

