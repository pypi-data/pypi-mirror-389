"""
Local coordinator for development purposes.
This is a simplified version of the real coordinator that acts as a proxy between the client and the local runtime.
"""

import asyncio
import json
import logging
import time
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import aiohttp

logger = logging.getLogger(__name__)


class LocalCoordinator:
    """
    A simplified coordinator for local development that:
    1. Accepts WebSocket connections at /ws
    2. Proxies session setup to the local runtime
    3. Sends LiveKit tokens back to clients
    4. Manages session lifecycle (start/stop)
    """
    
    def __init__(self, runtime_host: str, runtime_port: int):
        self.runtime_host = runtime_host
        self.runtime_port = runtime_port
        self.coordinator_port = 8080  # Always 8080
        self.runtime_base_url = f"http://{runtime_host}:{runtime_port}"
        
        # Track active connections
        self.active_connections: dict[str, WebSocket] = {}  # connection_id -> websocket
        
        # FastAPI app setup
        self.app = FastAPI(title="Local Reactor Coordinator")
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Handle WebSocket connection (no authentication for local dev)"""
            await self._handle_websocket_connection(websocket)
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "active_connections": len(self.active_connections),
                "runtime": f"{self.runtime_base_url}"
            }
    
    async def _handle_websocket_connection(self, websocket: WebSocket):
        """Handle WebSocket connection"""
        connection_id = str(uuid.uuid4())
        
        try:
            # Accept the connection
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            
            logger.info(f"Client connected (ID: {connection_id})")
            
            # Send welcome message
            welcome_msg = {
                "type": "welcome",
                "data": {
                    "message": f"Connected to Reactor Local Coordinator. Session: {connection_id[:8]}...",
                    "timestamp": time.time()
                }
            }
            await websocket.send_text(json.dumps(welcome_msg))
            
            # Handle incoming messages
            while True:
                data = await websocket.receive_text()
                logger.info(f"Received from client {connection_id}: {data}")
                
                try:
                    parsed_data = json.loads(data)
                    
                    # Handle sessionSetup message
                    if parsed_data.get("type") == "sessionSetup":
                        await self._handle_session_setup(connection_id, parsed_data, websocket)
                    else:
                        # Echo back unknown messages
                        echo_msg = {
                            "type": "echo",
                            "data": {
                                "echo": parsed_data,
                                "timestamp": time.time()
                            }
                        }
                        await websocket.send_text(json.dumps(echo_msg))
                        
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON message from {connection_id}: {data}")
                    
        except WebSocketDisconnect:
            logger.info(f"Client disconnected (ID: {connection_id})")
            await self._disconnect_client(connection_id)
        except Exception as e:
            logger.error(f"WebSocket error (ID: {connection_id}): {e}", exc_info=True)
            await self._disconnect_client(connection_id)
    
    async def _handle_session_setup(self, connection_id: str, message_data: dict, websocket: WebSocket):
        """
        Handle sessionSetup message:
        1. Call POST /start_session on runtime
        2. Get the LiveKit JWT token
        3. Send gpu-machine-assigned message to client
        """
        try:
            data = message_data.get("data", {})
            model_name = data.get("modelName")
            model_version = data.get("modelVersion")
            
            logger.info(f"Session setup for {connection_id}: model={model_name}:{model_version}")
            
            # Call start_session on the runtime
            timeout = aiohttp.ClientTimeout(total=30.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.runtime_base_url}/start_session") as response:
                    response.raise_for_status()
                    
                    # The response is the client token (JWT)
                    client_token = await response.text()
                    client_token = client_token.strip('"')  # Remove quotes if JSON string
                    
                    logger.info(f"Session started successfully for {connection_id}")
                    
                    # Send gpu-machine-assigned message with LiveKit details
                    assignment_msg = {
                        "type": "gpu-machine-assigned",
                        "data": {
                            "livekitWsUrl": "ws://localhost:7880",
                            "livekitJwtToken": client_token
                        }
                    }
                    await websocket.send_text(json.dumps(assignment_msg))
                    logger.info(f"Sent session assignment to client {connection_id}")
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to start session on runtime: {e}")
            # Send error message to client
            error_msg = {
                "type": "echo",
                "data": {
                    "echo": {"error": f"Failed to start session: {str(e)}"},
                    "timestamp": time.time()
                }
            }
            await websocket.send_text(json.dumps(error_msg))
        except Exception as e:
            logger.error(f"Error during session setup: {e}")
    
    async def _disconnect_client(self, connection_id: str):
        """
        Handle client disconnection:
        1. Call POST /stop_session on runtime
        2. Clean up connection tracking
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Call stop_session on the runtime
        try:
            timeout = aiohttp.ClientTimeout(total=10.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.runtime_base_url}/stop_session") as response:
                    response.raise_for_status()
                    logger.info(f"Session stopped successfully for {connection_id}")
        except aiohttp.ClientError as e:
            logger.warning(f"Failed to stop session on runtime: {e}")
        except Exception as e:
            logger.error(f"Error stopping session: {e}")
    
    async def start(self):
        """Start the local coordinator server"""
        logger.info(f"Starting Reactor Local Coordinator on 0.0.0.0:{self.coordinator_port}")
        logger.info(f"WebSocket endpoint: ws://localhost:{self.coordinator_port}/ws")
        logger.info(f"Runtime endpoint: {self.runtime_base_url}")
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.coordinator_port,
            log_level="info",
            ws_ping_interval=5,
            ws_ping_timeout=5,
            access_log=False
        )
        server = uvicorn.Server(config)
        
        try:
            await server.serve()
        except KeyboardInterrupt:
            logger.info("\nReceived shutdown signal (Ctrl+C)")
            logger.info("Reactor Local Coordinator stopped")


async def serve(runtime_port: int = 8081) -> None:
    """
    Start the Reactor Local Coordinator server on port 8080.
    
    Args:
        runtime_port: Port where the Reactor Local Runtime is running
    """
    coordinator = LocalCoordinator(
        runtime_host="localhost",
        runtime_port=runtime_port
    )
    await coordinator.start()


def main():
    """Entry point for running the Reactor Local Coordinator as a standalone process"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Reactor Local Coordinator')
    parser.add_argument('--runtime-port', type=int, default=8081, 
                        help='Port where the Reactor Local Runtime is running')
    
    args = parser.parse_args()
    
    asyncio.run(serve(runtime_port=args.runtime_port))


if __name__ == '__main__':
    main()

