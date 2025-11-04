import queue
import time
from typing import Optional
import numpy as np
import logging


STARTING_FPS_GUESS = 16
logger = logging.getLogger(__name__)



class FrameBuffer:
	def __init__(self, maxsize: int = 2, fps_debuff_factor: float = 1.0):
		self._q: "queue.Queue[Optional[np.ndarray]]" = queue.Queue(maxsize=maxsize)
		self._counter = 0
		self._monitoring_active = False
		self._last_block_time = None
		self.fps = None
		self.fps_debuff_factor = fps_debuff_factor
		logger.info(f"Frame Buffer initialized with fps_debuff_factor: {fps_debuff_factor}")
		
	def enable_monitoring(self):
		"""
		This command enables FPS monitoring and live changing. When a model is emitting blocks of frames,
		this should be called beforehand, to adapt the FPS to try and show these frames smoothly.
		In this case the enable monitoring should be called again before the next block is generated, so we can use the time o the call
		to already estimate the fps.
		"""
		if self._monitoring_active is False:
			self._monitoring_active = True
			self._last_block_time = time.perf_counter()

	def disable_monitoring(self):
		"""
		If the model stops emitting frames we cause the timing setup to fallback to the previous fps estimate.
		"""
		self._last_block_time = None
		self._monitoring_active = False

	def push(self, frames: Optional[np.ndarray]) -> None:
		"""
		Push frames to the frame buffer.
		The frames MUST be a NumPy ndarray instance. If None, the frame buffer will put the None through in the frame, allowing the video streamer to send a black frame.
		- Dimensions should be (H, W, C) for a single frame, or (N, H, W, C) for multiple frames.
		Args:
			frames: A single ndarray containing one or more frames.
		"""

		if frames is None:
			self._q.put_nowait(None)
			return

		# Extract individual frames from the ndarray
		if frames.ndim == 4:  # (N, H, W, C)
			individual_frames = list(frames)  # (N, H, W, C) ->  list of (H, W, C) frames
			total_frames = frames.shape[0]
		elif frames.ndim == 3:  # (H, W, C)
			individual_frames = [frames]
			total_frames = 1
		else:
			raise ValueError(f"Unsupported frame dimensions: {frames.shape}. Expected (H, W, C) or (N, H, W, C)")
			
		# Calculate total number of frames for FPS calculation
		if not self._last_block_time:
			if self.fps is None:
				self.fps = STARTING_FPS_GUESS
		else:
			block_generation_time = time.perf_counter() - self._last_block_time
			if self._q.qsize() > 2:
				# If the buffer size is starting to accumulate, we calculate the FPS so that we know we'll empty the buffer by the next block time.
				self.fps = ((total_frames + self._q.qsize())-1) / block_generation_time
			else:
				self.fps = (total_frames / block_generation_time) * self.fps_debuff_factor
			logger.debug(f"Block generation time: {block_generation_time}")
			logger.debug(f"Total frames processed: {total_frames}")
			#logger.info(f"Estimated FPS: {self.fps}")
		
		self._last_block_time = time.perf_counter()
		
		# Process each individual frame
		for frame in individual_frames:
			try:
				self._q.put_nowait(frame)
			except queue.Full:
				# drop-oldest
				try:
					self._q.get_nowait()
				except queue.Empty:
					pass
				try:
					self._q.put_nowait(frame)
				except queue.Full:
					pass

	def estimated_fps(self) -> int:
		"""Base FPS estimate from historical data."""
		if not self.fps:
			return STARTING_FPS_GUESS  # This is a baseline prediction, we improve with data over time.
		return self.fps

	def get_nowait(self) -> Optional[np.ndarray]:
		"""Get a frame from the buffer without blocking."""
		return self._q.get_nowait()

	def clear(self) -> None:
		"""Clear all frames from the buffer."""
		while True:
			try:
				self._q.get_nowait()
			except queue.Empty:
				break

	def is_monitoring_active(self) -> bool:
		return self._monitoring_active

