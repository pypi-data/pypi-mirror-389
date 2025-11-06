"""
Template showing how to integrate existing ML models into VideoModel interface.

"""
import queue
import random
import time
from typing import Tuple
import numpy as np
from PIL import Image, ImageDraw
from pydantic import Field
import logging
from reactor_runtime import VideoModel, command, get_ctx

logger = logging.getLogger(__name__)

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
        self._pipeline._paused = True

    @command("resume", description="Resume frame generation")
    def resume_command(self):
        """Resume the video generation."""
        self._pipeline._paused = False

    @command("set_brightness", description="Adjust brightness multiplier")
    def set_brightness_command(self, brightness: float = Field(..., ge=0.0, le=2.0, description="Brightness multiplier 0.0-2.0")):
        """Set the brightness multiplier for generated frames."""
        self._pipeline._brightness_multiplier = brightness
        logger.debug(f"Brightness set to {brightness}")

    def __init__(self, fps: int = 30, size: Tuple[int, int] = (480, 640), **kwargs):
        """Initialize model. Heavy weight loading happens here during container startup, before any user connects."""
        self._fps = max(1, int(fps))
        self._running = False
        self._paused = False
        self._frame_count = 0
        
        # Most common pattern: wrap existing model pipeline
        logger.debug("Initializing TemplateVideoModel...")
        self._pipeline = ExampleModelPipeline(fps=self._fps, size=size)
        logger.debug("TemplateVideoModel initialization complete")


    def start_session(self) -> None:
        """
        Start the video model's main processing loop.
        
        This method should assume that the model was already loaded in memory, and it should simply
        start it's inner loop, also making available the emit_frame function for pushing frames.
        
        This demonstrates the most common integration pattern: delegating to an existing model pipeline
        that handles frame generation and emission.
        """
        self._running = True
        self._paused = False
        
        logger.debug("Starting user session...")
        
        try:
            self._pipeline.run()
            
        except Exception as e:
            self._running = False
            time.sleep(2) #fake machine resetting time
            raise e
        finally:
            time.sleep(2) #fake machine resetting time
            self._running = False
            logger.debug("Model session ended.")



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
        self._queue = queue.Queue()
        self._paused = False
        
        # Simulate loading model weights - this represents the heavy initialization
        # that should happen once when the container starts up, not per session
        logger.info("Loading model weights...")
        loading_time = random.uniform(1.0, 5.0)  # Simulate weight loading
        time.sleep(loading_time)
        logger.info(f"Model weights loaded in {loading_time:.2f} seconds")
        
    def reset_session_state(self):
        """
        Reset the model to initial state for a new session.
        
        This demonstrates what should happen in stop_session() - reset user inputs
        and conditioning without unloading the heavy model weights.
        """
        logger.info("Resetting model session state...")
        
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
        logger.info("Session state reset complete")

    def run(self):
        """
        Main blocking processing loop.
        """
        self._running = True
        frame_interval = 1.0 / self._fps
        
        get_ctx().enable_monitoring()
        try:
            while self._running:
                start_time = time.time()
                if get_ctx()._stop_evt.is_set():
                    break

                if self._paused:
                    elapsed = time.time() - start_time
                    sleep_duration = max(0.0, frame_interval - elapsed)
                    if sleep_duration > 0:
                        time.sleep(sleep_duration)
                    continue
                
                self._frame_count += 1

                frame = self._generate_frame_with_counter()
                get_ctx().emit_block(frame)

                
                

                
                # Maintain target FPS
                elapsed = time.time() - start_time
                sleep_duration = max(0.0, frame_interval - elapsed)
                if get_ctx()._stop_evt.is_set():
                    break
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                    
        except Exception as e:
            self.reset_session_state()
            self._running = False
            raise e
        finally:
            # REALLY IMPORTANT!! Reset the session state when the loop exits.
            # The model should be back clean and available for the next user.
            self.reset_session_state()
            self._running = False


    def stop(self):
        """Stop the pipeline processing loop."""
        self._running = False

    def _generate_frame_with_counter(self) -> np.ndarray:
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
        
        return img_with_text
