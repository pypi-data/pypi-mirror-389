

import asyncio
import threading
import time
from typing import Tuple
from livekit import rtc
import numpy as np
from reactor_runtime.output.frame_buffer import FrameBuffer
import logging
try:
	from reactor_runtime.context._cloud.reactor_machine_metrics import ReactorMachineMetrics
except ImportError:
	ReactorMachineMetrics = None
from reactor_runtime.output.streamer import Streamer

logger = logging.getLogger(__name__)


def convert_frame_to_livekit(frame: np.ndarray):
	"""Convert np.ndarray to LiveKit VideoFrame"""
	# Convert to numpy array
	height, width = frame.shape[:2]

	# Create LiveKit frame
	lk_frame = rtc.VideoFrame(width, height, rtc.VideoBufferType.RGB24, frame.tobytes())
	return lk_frame

class LivekitVideoStreamer(Streamer):
	"""
	Frame streamer that pulls frames from a FrameBuffer and emits them at 13 FPS.
	Handles empty buffer (reuse old frame) and None values (black frame).
	"""

	def __init__(self, frame_buffer: FrameBuffer, resolution: Tuple[int, int] = (720, 480)):
		super().__init__(frame_buffer, resolution)

		self.room: rtc.Room = None
		self.video_source = rtc.VideoSource(resolution[0], resolution[1])  
		self.video_track = rtc.LocalVideoTrack.create_video_track("reactor-video", self.video_source)
		self.options = rtc.TrackPublishOptions(
			source=rtc.TrackSource.SOURCE_CAMERA,
			simulcast=True,
			video_encoding=rtc.VideoEncoding(
				max_framerate=60,
				max_bitrate=1000000,
			),
		)

	def set_room(self, room: rtc.Room):
		"""Set the LiveKit room to stream to"""
		self.room = room

	async def start_streaming(self):
		"""Start the frame streaming loop"""

		if self.room is None:
			raise RuntimeError("LK Room not set. First call set_room()")

		with self._lock:
			if not self._running:
				self._running = True
			else:
				return
		
		await self.room.local_participant.publish_track(self.video_track, self.options)
		self._stream_thread = threading.Thread(target=self._stream_loop, daemon=False)
		self._stream_thread.start()

	async def stop_streaming(self):
		if not self._running or self.room is None:
			return

		"""Stop the frame streaming loop"""
		self._running = False
		
		# Wait for thread to finish (with timeout)
		if self._stream_thread and self._stream_thread.is_alive():
			self._stream_thread.join(timeout=0.5)  # Reduced timeout since thread should exit quickly now
			if self._stream_thread.is_alive():
				logger.warning("Stream thread did not stop within timeout - this should not happen with the new exit checks")
		self._stream_thread = None

		try:
			await asyncio.wait_for(
				self.room.local_participant.unpublish_track(self.video_track.sid),
				timeout=10.0
			)
		except (asyncio.TimeoutError, Exception) as e:
			logger.warning(f"Track unpublish timed out: {e}")
		logger.debug("Stopped frame streaming loop")
		self.room = None

	def _stream_loop(self):
		"""Main streaming loop that runs in a separate thread"""
		frame_interval = 1.0 / self.frame_buffer.estimated_fps()  # ~0.077 seconds between frames
		frame_count = 0
		
		logger.debug("Video stream thread started")
		
		while self._running:
			# Check exit condition at start of each iteration
			if not self._running:
				break
				
			frame_interval = 1.0 / self.frame_buffer.estimated_fps()
			start_time = time.perf_counter()
			frame_count += 1

			if frame_count % 100 == 0 and ReactorMachineMetrics is not None:
				ReactorMachineMetrics.set_gauge("model_fps", self.frame_buffer.estimated_fps())
			
			try:
				# Try to get a frame from the buffer
				frame = self.frame_buffer.get_nowait()

				if frame is None:
					# Buffer has None -> send black frame
					h, w = self._fallback_size
					black = np.zeros((h, w, 3), dtype=np.uint8)
					frame_to_send = black
					self._previous_frame = None
				else:
					frame_to_send = frame
					self._previous_frame = frame_to_send
			except Exception as e:
				# Buffer empty -> reuse previous frame or create black frame
				if self._previous_frame is not None:
					# Reuse previous frame
					frame_to_send = self._previous_frame
				else:
					# No previous frame -> create black frame
					h, w = self._fallback_size
					black = np.zeros((h, w, 3), dtype=np.uint8)
					frame_to_send = black

			# Check exit condition before video processing
			if not self._running:
				break

			# Convert and send frame to LiveKit
			try:
				if self.video_source is None:
					logger.warning("Warning: video_source is None, skipping frame")
					continue

				# Check exit condition before potentially blocking call
				if not self._running:
					break
					
				# LiveKit's capture_frame is synchronous
				self.video_source.capture_frame(convert_frame_to_livekit(frame_to_send))
			except Exception as e:
				logger.error(f"Error sending frame to LiveKit: {e}")

			# Check exit condition before sleep
			if not self._running:
				break

			# Wait for next frame time with interruptible sleep
			elapsed = time.perf_counter() - start_time
			sleep_time = max(0, frame_interval - elapsed)
			if sleep_time > 0:
				# Break sleep into smaller chunks to allow for more responsive exit
				sleep_chunk = 0.01  # 10ms chunks
				remaining_sleep = sleep_time
				while remaining_sleep > 0 and self._running:
					chunk_sleep = min(sleep_chunk, remaining_sleep)
					time.sleep(chunk_sleep)
					remaining_sleep -= chunk_sleep
		
		logger.debug("Video stream thread exiting")
