


import asyncio
from typing import Dict, Callable, Optional
import numpy as np
from livekit import rtc
from livekit.rtc import VideoStream
import logging

logger = logging.getLogger(__name__)

class InputVideoHandler:
    def __init__(self):
        self.video_tracks: Dict[str, rtc.Track]  = {}  # track_sid -> track
        self.video_stream_tasks: Dict[str, asyncio.Task] = {}  # track_sid -> task
        self.on_frame_callback: Optional[Callable[[np.ndarray], None]] = None
        self.enabled = False

    def set_on_frame_callback(self, callback: Callable[[np.ndarray], None]):
        self.on_frame_callback = callback
        self.enabled = True
        
    async def start_input_video_handler(self, track: rtc.RemoteVideoTrack):
        if not self.enabled:
            return

        if track.sid in self.video_tracks:
            return

        if track.kind != rtc.TrackKind.KIND_VIDEO:
            return
        
        self.video_tracks[track.sid] = track
        video_stream = VideoStream(track)
        
        # Create and store the task that processes video frames
        task = asyncio.create_task(self._process_video_stream(track.sid, video_stream))
        self.video_stream_tasks[track.sid] = task
    
    async def _process_video_stream(self, track_sid: str, video_stream: VideoStream):
        """Process incoming video frames from the stream"""
        if not self.enabled:
            return

        try:
            async for event in video_stream:
                frame = event.frame
                if self.on_frame_callback is None:
                    continue
                result = self.convert_frame(frame)
                self.on_frame_callback(result)
        except asyncio.CancelledError:
            logger.info(f"Video stream processing cancelled for track {track_sid}")
        except Exception as e:
            logger.error(f"Error processing video stream for track {track_sid}: {e}")
        finally:
            # Clean up the video stream
            await video_stream.aclose()

    def cleanup(self):
        for task in self.video_stream_tasks.values():
            task.cancel()
        self.video_stream_tasks.clear()
        self.video_tracks.clear()

    
    def stop_input_video_handler(self, track_sid: str):
        """
        Handles the unsubscription of a video track.
        Stops the video stream processing for the track.
        Stops the tasks that were running in a loop.
        """
        if not self.enabled:
            return

        # Cancel the video stream task if it exists
        if track_sid in self.video_stream_tasks:
            task = self.video_stream_tasks[track_sid]
            task.cancel()
            del self.video_stream_tasks[track_sid]
        
        if track_sid in self.video_tracks:
            del self.video_tracks[track_sid]

    def convert_frame(self, frame: rtc.VideoFrame) -> np.ndarray:
        # Convert LiveKit VideoFrame to np.ndarray
        # Convert to RGB24 format and get raw data
        rgb_frame = frame.convert(rtc.VideoBufferType.RGB24)
        
        # Convert bytes to numpy array and reshape to (height, width, 3)
        frame_array = np.frombuffer(rgb_frame.data, dtype=np.uint8).reshape(
            (frame.height, frame.width, 3)
        )
        
        return frame_array
