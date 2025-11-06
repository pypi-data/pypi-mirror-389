import asyncio
import json
import logging
import os
import subprocess
import threading
from typing import Tuple
from fastapi import FastAPI, HTTPException
from livekit import rtc
from reactor_runtime.context.abstract_runtime import Runtime
from reactor_runtime.context.context import _set_global_ctx
from reactor_runtime.context.local.utils import start_livekit_dev
from reactor_runtime.context.local.local_coordinator import LocalCoordinator
from reactor_runtime.livekit.livekit import build_livekit_config, create_access_token
from reactor_runtime.output.video_streamer import LivekitVideoStreamer
import uvicorn

logger = logging.getLogger(__name__)


class LocalRuntime(Runtime):
    def __init__(self, model_name: str, model_args: dict, model_version: str, host: str, port: int):
        super().__init__(model_name, model_args, model_version, host, port)
        lk_url = "ws://localhost:7880"
        lk_api_key = "devkey"
        lk_api_secret = "secret"
        self.lk_config = build_livekit_config(livekit_url=lk_url, livekit_api_key=lk_api_key, livekit_api_secret=lk_api_secret)

    async def connect_to_room(self, jwt_token: str, ws_url: str, session_id: str) -> Tuple[rtc.Room, LivekitVideoStreamer]:
        """
        Generates a token for the runtime to connect to the room.
        Generates a token for the client to connect to the room. (dev feature)
        Registers event handlers for the room.
        Connects to the room.
        Starts the video streaming.
        """
        try:
            logger.info(f"Connecting to room")
            room = rtc.Room()
            self.room = room
            self.video_streamer = LivekitVideoStreamer(self.frame_buffer)

            # Set up event handlers
            @room.on("participant_connected")
            def on_participant_connected(participant: rtc.Participant):
                logger.info(f"Participant connected: {participant.identity}")

            @room.on("participant_disconnected") 
            def on_participant_disconnected(participant):
                logger.info(f"Participant disconnected: {participant.identity}. Reason: {participant.disconnect_reason}")
                self._create_task(self.stop_session(session_id), name="stop_session")

            @room.on("track_subscribed")
            def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.Participant):
                logger.info(f"Track subscribed: {track.kind} by {participant.identity}")
                if self.input_video_handler:
                    # This is async because it needs to start the stream loop on the main asyncio context.
                    self._create_task(self.input_video_handler.start_input_video_handler(track), name="on_track_subscribed")

            @room.on("track_unsubscribed")
            def on_track_unsubscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.Participant):
                logger.info(f"Track unsubscribed: {track.kind} by {participant.identity}")
                if self.input_video_handler:
                    self.input_video_handler.stop_input_video_handler(track.sid)

            def handle_data_received(reader, participant_identity):
                async def process_text_from_reader(reader):
                    text = await reader.read_all()
                    # React on data received.
                    await self._dispatch_app_message(text)

                self._create_task(process_text_from_reader(reader), name="process_text_from_reader")

            room.register_text_stream_handler("application", handle_data_received)
            self.video_streamer.set_room(room)
            await room.connect(ws_url, jwt_token)
            await self.video_streamer.start_streaming()
        except Exception as e:
            raise Exception(f"Failed to connect to room: {e}")


    async def send_out_app_message(self, data: dict) -> None:
        """
        Sends a message to the client.
        """
        if not self.room:
            raise RuntimeError("Cannot send app message - not connected to room.")
        try:
            await self.room.local_participant.send_text(json.dumps(data), topic="application")
        except Exception as e:
            logger.exception(f"Failed to send app message: {e}")

    async def start_session(self, lk_jwt: str, lk_url: str, lk_session_id : str) -> None:
        async with self.session_lock:
            if not self.model_loaded:
                raise RuntimeError("Model not loaded. Call load_model() first.")
            if self.session_id is not None:
                raise RuntimeError("Session already started. Call stop_session() first.")
            try:
                self.session_id = lk_session_id
                ctx = self._build_context()
                _set_global_ctx(ctx)
                await self.connect_to_room(lk_jwt, lk_url, lk_session_id)
                self._create_task(self._start_model_lifecycle(), name="start_model_lifecycle")
                logger.info(f"Session {lk_session_id} started successfully, releasing lock")
            except Exception as e:
                # Comprehensive cleanup on session start failure
                logger.error(f"Session start failed: {e}")
                # Re-raise to propagate to HTTP endpoint
                raise

        
    async def stop_session(self, lk_session_id: str) -> None:
        async with self.session_lock:
            if self.session_id is None:
                raise RuntimeError("Session not started. Call start_session() first.")
            self.session_id = None
            if self.video_streamer:
                await self.video_streamer.stop_streaming()
                self.video_streamer = None
            if self.room:
                logger.info(f"Disconnecting from room...")
                self._create_task(self.room.disconnect(), name="room_disconnect")
            if self.input_video_handler:
                self.input_video_handler.cleanup()
            if self.stop_evt:
                # Set the stop event, which is the signal used for the model thread to exit.
                # The model should cooperatively exit.
                self.stop_evt.set()
            await self._wait_for_model_thread()
            self.model_thread = None
            await self._cancel_all_tasks()
            self.cancel_room_listeners(self.loop)
            _set_global_ctx(None)
            self.frame_buffer.clear()


async def serve(model_spec: str, model_name: str, model_args: str, model_version: str, host: str = "0.0.0.0", port: int = 8081) -> None:
    """
    Start a model in a local environment with a local coordinator.
    This starts:
    1. LiveKit server (port 7880)
    2. Local runtime with HTTP endpoints (specified port, default 8081)
    3. Local coordinator with WebSocket endpoint at /ws (always port 8080)
    """
    model_args_dict = json.loads(model_args) if model_args else {}
    
    # Start LiveKit process
    lk_process = start_livekit_dev()
    
    # Create runtime
    runtime = LocalRuntime(model_name=model_name, model_args=model_args_dict, model_version=model_version, host=host, port=port)
    model_thread = threading.Thread(target=runtime.load_model, args=(model_spec, model_args_dict), daemon=False)
    model_thread.start()

    # Create runtime FastAPI app
    runtime_app = FastAPI()

    @runtime_app.post("/start_session")
    async def start_session() -> None:
        try:
            session_id = "local"
            lk_jwt = await create_access_token(runtime.lk_config, session_id, participant_name="reactor-server")
            client_token = await create_access_token(runtime.lk_config, session_id, client_token=True, participant_name="reactor-client")
            await runtime.start_session(lk_jwt=lk_jwt, lk_url=runtime.lk_config.ws_url, lk_session_id=session_id)
            return client_token
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @runtime_app.post("/stop_session")
    async def stop_session() -> None:
        try:
            await runtime.stop_session(None)
        except Exception as e:
            logger.error(f"Error stopping session: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Create local coordinator (always on port 8080)
    coordinator = LocalCoordinator(
        runtime_host=host,
        runtime_port=port
    )
    
    # Configure runtime server
    runtime_config = uvicorn.Config(
        app=runtime_app,
        host=host,
        port=port,
        log_level="info",
        access_log=False
    )
    runtime_server = uvicorn.Server(runtime_config)
    
    # Run both servers concurrently
    try:
        await asyncio.gather(
            runtime_server.serve(),
            coordinator.start()
        )
    except KeyboardInterrupt:
        logger.info("\nShutdown signal received, cleaning up...")
        lk_process.terminate()
        lk_process.wait(timeout=5)
        if runtime.model_thread and runtime.model_thread.is_alive():
            runtime.stop_evt.set()
            await runtime._wait_for_model_thread(5)
        logger.info("Cleanup complete")