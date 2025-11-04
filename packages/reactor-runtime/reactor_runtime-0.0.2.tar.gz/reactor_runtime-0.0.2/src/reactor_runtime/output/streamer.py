



from abc import ABC, abstractmethod
import threading
from typing import Optional, Tuple

import av
from reactor_runtime.output.frame_buffer import FrameBuffer


class Streamer(ABC):
	def __init__(self, frame_buffer: FrameBuffer, resolution: Tuple[int, int] = (720, 480)):
		self.frame_buffer = frame_buffer
		self.frame_buffer.clear()
		self.resolution = resolution
		self._lock = threading.Lock()

		self._previous_frame: Optional[av.VideoFrame] = None
		self._resolution = resolution
		self._fallback_size = (resolution[1], resolution[0])  # (height, width) for fallback frames
		self._running = False
		self._stream_thread: Optional[threading.Thread] = None

	@abstractmethod
	async def start_streaming(self):
		pass

	@abstractmethod
	async def stop_streaming(self):
		pass