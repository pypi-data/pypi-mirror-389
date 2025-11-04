"""
Template showing how to integrate existing ML models into VideoModel interface.

"""

import asyncio
import random
import time
from typing import Any, List, Optional, Tuple

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

from reactor_runtime import VideoModel, command, get_ctx


class TemplateVideoModel(VideoModel):
    """
    Template showing integration of existing ML models with VideoModel interface.
    
    Demonstrates:
    - Method-based command system with automatic schema generation
    - Model pipeline integration pattern
    - Async session management
    - Proper state reset between sessions
    """

    name: str = "template-video"

    @command("pause", description="Pause frame generation")
    def pause_command(self):
        """Pause the video generation."""
        self._paused = True

    @command("resume", description="Resume frame generation")
    def resume_command(self):
        """Resume the video generation."""
        self._paused = False

    @command("set_brightness", description="Adjust brightness multiplier")
    def set_brightness_command(self, brightness: float = Field(..., ge=0.0, le=2.0, description="Brightness multiplier 0.0-2.0")):
        """Set the brightness multiplier for generated frames."""
        self._pipeline._brightness_multiplier = brightness
        print(f"Brightness set to {brightness}")


    def __init__(self, fps: int = 30, size: Tuple[int, int] = (480, 640), **kwargs):
        """Initialize model. Heavy weight loading happens here during container startup, before any user connects."""
        self._fps = max(1, int(fps))
        self._height, self._width = size
        self._running = False
        self._paused = False
        self._frame_count = 0
        
        # Most common pattern: wrap existing model pipeline
        print("Initializing TemplateVideoModel...")
        self._pipeline = ExampleModelPipeline(fps=self._fps, size=size)
        print("TemplateVideoModel initialization complete")


    async def start_session(self) -> None:
        """
        Start the video model's main processing loop.
        
        This method should assume that the model was already loaded in memory, and it should simply
        start it's inner loop, also making available the emit_frame function for pushing frames.
        
        This demonstrates the most common integration pattern: delegating to an existing model pipeline
        that handles frame generation and emission.
        """
        self._running = True
        self._paused = False
        
        print("Starting user session...")
        
        try:
            # Delegate to pipeline - note: making run() async is an adaptation
            # needed for the runtime. Most ML models aren't naturally async, but will need
            # to be adapted to the runtime.
            await self._pipeline.run()
            
        except Exception as e:
            print(f"Error during session: {e}")
        finally:
            self._running = False
            print("User session ended")


    async def stop_session(self) -> None:
        """
        Stop the video model and clean up inputs and output stream from the user's session.
        
        This should pause the inference, bring it to a reset initial state as quickly as possible,
        to allow the next user to connect. This should NOT unload models from memory or cleanup the model.

        You should assume that calls to "start_session()" and "stop_session()" will happen in sequence,
        and time in between them should be as low as possible.
        
        This demonstrates the proper way to reset model state between sessions without 
        unloading heavy model weights.
        """
        print("Stopping user session...")
        
        self._running = False
            
        self._pipeline.stop()
        
        # Reset the pipeline to initial state for the next session
        # This is crucial: reset user inputs and conditioning without unloading weights
        self._pipeline.reset_session_state()
        
        # Reset VideoModel state
        self._paused = False
        self._frame_count = 0
        
        print("Session stopped and reset for next user")




class ExampleModelPipeline:
    """
    Example model pipeline that simulates a typical ML model integration.
    
    This demonstrates how to wrap an existing model into the VideoModel interface,
    which is the most common use case when integrating pre-existing models.
    """
    
    def __init__(self, fps: int = 30, size: Tuple[int, int] = (480, 640)):
        """Initialize pipeline and simulate weight loading."""
        self._fps = fps
        self._height, self._width = size
        self._frame_count = 0
        self._running = False
        self._brightness_multiplier: float = 1.0
        
        # Simulate loading model weights - this represents the heavy initialization
        # that should happen once when the container starts up, not per session
        print("Loading model weights...")
        loading_time = random.uniform(1.0, 5.0)  # Simulate weight loading
        time.sleep(loading_time)
        print(f"Model weights loaded in {loading_time:.2f} seconds")
        
    def reset_session_state(self):
        """
        Reset the model to initial state for a new session.
        
        This demonstrates what should happen in stop_session() - reset user inputs
        and conditioning without unloading the heavy model weights.
        """
        print("Resetting model session state...")
        
        # Reset user inputs
        self._frame_count = 0
        self._brightness_multiplier = 1.0
        get_ctx().disable_monitoring()
        
        # In real models, also reset:
        # - conditioning latents 
        # - user prompt embeddings
        # - previous frame cache
        # - anything else leftover from the session.
        
        self._running = False
        print("Session state reset complete")

    async def run(self):
        """
        Main blocking processing loop. Note: making this async is an adaptation for the runtime.
        Most ML models aren't naturally async, but this is needed for integration.
        """
        self._running = True
        frame_interval = 1.0 / self._fps
        
        get_ctx().enable_monitoring()
        try:
            while self._running:
                start_time = time.time()
                
                frame = self._generate_frame_with_counter()

                # Emit the frame (this is how you integrate with existing models)
                await get_ctx().emit_block(frame)
                
                self._frame_count += 1
                
                # Maintain target FPS
                elapsed = time.time() - start_time
                sleep_duration = max(0.0, frame_interval - elapsed)
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)
                    
        except Exception as e:
            print(f"Error in model pipeline: {e}")
        finally:
            self._running = False


    def stop(self):
        """Stop the pipeline processing loop."""
        self._running = False

    def _generate_frame_with_counter(self) -> av.VideoFrame:
        """Generate frame with counter overlay for visual feedback."""
        h, w = self._height, self._width
        
        img = np.zeros((h, w, 3), dtype=np.uint8)
        
        for y in range(h):
            intensity = int((y / h) * 255)
            img[y, :, 0] = intensity
        
        offset = int((self._frame_count * 2)) % w
        bar_width = max(1, w // 20)
        
        x_start = offset
        x_end = min(w, x_start + bar_width)
        img[:, x_start:x_end, 1] = 255
        
        # Apply brightness multiplier to the entire image
        img = np.clip(img * self._brightness_multiplier, 0, 255).astype(np.uint8)
        
        # Add frame counter overlay
        pil_img = Image.fromarray(img)
        draw = ImageDraw.Draw(pil_img)
        
        counter_text = f"Frame: {self._frame_count}"
        text_x, text_y = 10, 10
        outline_color = (0, 0, 0)
        text_color = (255, 255, 255)
        
        # Draw outline for visibility
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    draw.text((text_x + dx, text_y + dy), counter_text, fill=outline_color)
        
        draw.text((text_x, text_y), counter_text, fill=text_color)
        
        img_with_text = np.array(pil_img)
        
        return av.VideoFrame.from_ndarray(img_with_text, format="rgb24")
