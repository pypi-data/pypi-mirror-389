from typing import Callable, Optional
from dataclasses import dataclass
from livekit import rtc, api
from livekit.api import DeleteRoomRequest
import logging

logger = logging.getLogger(__name__)

@dataclass
class LiveKitConfig:
    """Simple LiveKit configuration"""
    api_key: str
    api_secret: str
    ws_url: str

def build_livekit_config(
    livekit_url: Optional[str] = None,
    livekit_api_key: Optional[str] = None, 
    livekit_api_secret: Optional[str] = None,
) -> LiveKitConfig:
    """Build LiveKit configuration from parameters and environment"""


    if not livekit_api_key:
        raise ValueError("LIVEKIT_API_KEY must be provided as a parameter.")
    if not livekit_api_secret:
        raise ValueError("LIVEKIT_API_SECRET must be provided as a parameter.") 
    if not livekit_url:
        raise ValueError("LIVEKIT_WS_URL must be provided as a parameter.")

    return LiveKitConfig(
        api_key=livekit_api_key,
        api_secret=livekit_api_secret,
        ws_url=livekit_url
    )

async def create_access_token(config: LiveKitConfig, room_name: str, participant_name: str = "reactor-server", client_token: bool = False):
        
        if client_token:
            grants: api.VideoGrants = api.VideoGrants(
                room_join=True,
                room=room_name,
                room_create=False,
                can_publish=True,
            )
        else:
            grants: api.VideoGrants = api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_publish_data=True,
                    can_subscribe=True,
                    room_create=True
                )
        
        """Generate LiveKit access token"""
        token = (
            api.AccessToken(config.api_key, config.api_secret)
            .with_identity(participant_name)
            .with_name(participant_name)
            .with_grants(
                grants
            )
            .to_jwt()
        )
        return token

async def create_room(jwt_token: str, ws_url: str, session_id: str):
    """
    Connects to a LiveKit room, setting up hooks and starting the video streaming.
    """
    try:
        logger.info(f"Connecting to room")
        room = rtc.Room()

        # Set up event handlers
        @room.on("participant_connected")
        def on_participant_connected(participant: rtc.Participant):
            pass

        @room.on("participant_disconnected") 
        def on_participant_disconnected(participant):
            logger.info(f"Participant disconnected: {participant.identity}. Reason: {participant.disconnect_reason}")
            if participant.identity in self._participants:
                del self._participants[participant.identity]
                # React on participant disconnection. The session is over.
                logger.info(f"Stopping session because participant {participant.identity} disconnected.")
                self._create_task(self._stop_session(session_id), name="stop_session")

        @room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.Participant):
            logger.info(f"Track subscribed: {track.kind} by {participant.identity}")
            self._create_task(self.video_handler.on_track_subscribed(track), name="on_track_subscribed")

        @room.on("track_unsubscribed")
        def on_track_unsubscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.Participant):
            logger.info(f"Track unsubscribed: {track.kind} by {participant.identity}")
            self.video_handler.on_track_unsubscribed(track.sid)

        def handle_data_received(reader, participant_identity):
            async def process_text_from_reader(reader):
                text = await reader.read_all()
                # React on data received.
                logger.info(f"Received message: {text}")
                await self._dispatch_app_message(text)

            self._create_task(process_text_from_reader(reader), name="process_text_from_reader")

        room.register_text_stream_handler("application", handle_data_received)
        return room
        # await self.room.connect(ws_url, jwt_token)
        # await self.video_streamer.start_streaming(self.room)
    except Exception as e:
        raise Exception(f"Failed to connect to room: {e}")

async def delete_room(config: LiveKitConfig, room_name: str):
    """Delete a room from LiveKit by name"""
    async with api.LiveKitAPI(
        url=config.ws_url,
        api_key=config.api_key,
        api_secret=config.api_secret
    ) as lkapi:
        await lkapi.room.delete_room(DeleteRoomRequest(room=room_name))
