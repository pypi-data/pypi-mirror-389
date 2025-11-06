



from abc import ABC, abstractmethod
import asyncio
import json
import logging
import threading
from typing import Optional
import numpy as np

from reactor_runtime.utils.messages import ApplicationMessage
from reactor_runtime.context.context import ReactorContext
from reactor_runtime.input.input_video import InputVideoHandler
from reactor_runtime.model_api import VideoModel
from reactor_runtime.output.frame_buffer import FrameBuffer
from reactor_runtime.utils.loader import build_model

logger = logging.getLogger(__name__)

BUFFER_MAXSIZE = 50

class Runtime(ABC):
    def __init__(self, model_name: str, model_args: dict, model_version: str, host: str, port: int):
        self.ws_port = port
        self.host = host
        self.model_name = model_name
        self.model_args = model_args
        self.model_version = model_version
        self.model_loaded = False
        self.model = None
        self.model_thread = None
        self.session_id = None
        self.session_lock = asyncio.Lock()
        self.frame_buffer = FrameBuffer(maxsize=BUFFER_MAXSIZE, fps_debuff_factor=model_args.get("fps_debuff_factor", 1.0))
        self.stop_evt = None
        self.loop = asyncio.get_running_loop()
        self._bg_tasks: set[asyncio.Task] = set()
        self.video_streamer = None
        self.input_video_handler = None

    def load_model(self, model_spec: str, model_args: dict) -> None:
        model_instance: VideoModel = build_model(model_spec, model_args)
        if model_instance.manifest().get("video_input", False):
            logger.info("Model manifest accepts video input. Setting up video input.")
            self._setup_video_input(model_instance)
        self.model = model_instance
        self.model_loaded = True
        logger.info(f"Model {self.model_name} loaded successfully and now available for inference.")

    def _create_task(self, coro: asyncio.Future, name: str = "unnamed") -> asyncio.Task:
        task = self.loop.create_task(coro, name=name)
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)
        return task

    async def _start_model_lifecycle(self):
        """
        Starts the model in a separate thread. Wraps the thread call in a try/except block to catch any exceptions.
        Exceptions are then passed ot the on_model_exited callback, for proper handling.
        """

        error: Optional[Exception] = None
        def start_session_with_exception_handler() -> None:
            nonlocal error
            try:
                self.model.start_session()
            except Exception as e:
                logger.critical(f"Model Error: {e}", exc_info=True)
                error = e
        self.model_thread = threading.Thread(target=start_session_with_exception_handler, daemon=False)
        self.model_thread.start()
        await self._wait_for_model_thread()
        await self.on_model_exited(error)

    async def _wait_for_model_thread(self, timeout: Optional[float] = None) -> None:
        if self.model_thread is None or not self.model_thread.is_alive():
            return
        
        logger.debug(f"Waiting for model thread {self.model_thread.name} to exit...")
        
        async def wait_loop():
            while self.model_thread and self.model_thread.is_alive():
                await asyncio.sleep(0.1)
        
        try:
            if timeout is not None:
                await asyncio.wait_for(wait_loop(), timeout=timeout)
            else:
                await wait_loop()
            logger.debug("Model thread exited.")
        except asyncio.TimeoutError:
            logger.critical(f"Timeout waiting for model thread to exit after {timeout} seconds")
            raise
        finally:
            if self.model_thread and not self.model_thread.is_alive():
                self.model_thread = None
            logger.debug("Finished waiting for model thread.")

    def cancel_room_listeners(self, loop: asyncio.AbstractEventLoop):
        for task in asyncio.all_tasks(loop):
            coro = task.get_coro()
            if coro.__qualname__.startswith("Room._listen_task"):
                task.cancel()

    async def _cancel_all_tasks(self) -> None:
        """
        Cancel all background tasks and wait for them to complete.
        The function is blocking, and if any task hangs, it will hang with NO timeout.

        """
            
        # Get current task to avoid canceling ourselves
        current_task = asyncio.current_task()
        
        # Cancel all tasks except the current one
        tasks_to_cancel = []
        for t in list(self._bg_tasks):
            if t != current_task:
                t.cancel()
                tasks_to_cancel.append(t)
        
        # Wait for all canceled tasks to complete
        if tasks_to_cancel:
            try:
                await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            except Exception:
                raise RuntimeError("Error waiting for background tasks to complete")
        
        # Clear all tasks (including current task which will be removed when it completes)
        self._bg_tasks.clear()

    @abstractmethod
    async def send_out_app_message(self, data: ApplicationMessage) -> None:
        pass

    def _send_out_app_message(self, data: dict) -> None:
        """
        Emits event for sending app message on the main network loop.
        The message is wrapped in an ApplicationMessage envelope before sending.
        The message is going in direction model -> client.
        """
        wrapped = ApplicationMessage(data=data).model_dump()
        try:
            logger.info(f"Sending app message to client: {wrapped}")
            self.loop.create_task(self.send_out_app_message(wrapped))
        except Exception as e:
            logger.exception(f"Failed to send app message to client: {e}")

    def _emit_block(self, frames: Optional[np.ndarray]) -> None:
        """
        Emits event for emitting block on the main network loop.
        Frames should be a NumPy ndarray (H, W, 3) in RGB, or a stack of frames with the stack on the first dimension (N, H, W, 3).
        Can accept either a single frame or a list of frames.
        If None, the frame buffer will put the None through in the frame, allowing the video streamer to send a black frame.
        The frames are going in direction model -> client.
        """
        try:
            self.frame_buffer.push(frames)
        except Exception as e:
            logger.exception(f"Failed to emit block: {e}")

    def _build_context(self) -> ReactorContext:
        self.frame_buffer.clear()
        self.stop_evt = threading.Event()
        return ReactorContext(
            _send_fn=self._send_out_app_message,
            _emit_block_fn=self._emit_block,
            _enable_monitoring_fn=self.frame_buffer.enable_monitoring,
            _disable_monitoring_fn=self.frame_buffer.disable_monitoring,
            _stop_evt=self.stop_evt
        )

    async def _dispatch_app_message(self, message: str) -> None:
        """
        Pass an inbound message to the model after unwrapping an Application envelope if present.
        """
        raw = json.loads(message)

        # Unwrap simple envelope: { type: 'application', data: {...} }
        msg_type = raw.get("type")
        payload = raw.get("data") if msg_type == "application" else raw
        command = payload.get("type", "")
        command_data = payload.get("data", {})

        if command == "requestCapabilities":
            # Upon request of capabilities, send them back to the client.
            self._send_out_app_message(self.model.commands())

        try:
            self.model.send(command, command_data)
        except Exception:
            logger.error("App handle_message failed")

    async def on_model_exited(self, error: Optional[Exception]) -> None:
        if error:
            # Handle error in here. The call to critical happens in the model thread,
            # because we need to catch the logs stacktrace.
            logger.warning(f"Model exited with error: {error}")
        else:
            logger.info("Model exited. Stopping session.")
        await self.stop_session(None)

    def _setup_video_input(self, model: VideoModel) -> None:
        self.input_video_handler = InputVideoHandler()
        self.input_video_handler.set_on_frame_callback(model.on_frame)

    @abstractmethod
    async def start_session(self, lk_jwt: str, lk_url: str, lk_session_id: str) -> None:
        pass

    @abstractmethod
    async def stop_session(self, lk_session_id: str) -> None:
        pass

