from typing import List

from starlette.websockets import WebSocket

from skynet.logs import get_logger
from skynet.modules.stt.streaming_whisper.chunk import Chunk
from skynet.modules.stt.streaming_whisper.state import State
from skynet.modules.stt.streaming_whisper.utils import utils

log = get_logger(__name__)


class MeetingConnection:
    participants: dict[str, State] = {}
    previous_transcription_tokens: List[int]

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.previous_transcription_tokens = []

    async def connect(self):
        await self.websocket.accept()

    def disconnect(self):
        for participant_id in list(self.participants.keys()):
            self.remove_participant(participant_id)

    def add_participant(self, participant_id: str, language: str) -> None:
        if participant_id not in self.participants:
            self.participants[participant_id] = State(language)

    def remove_participant(self, participant_id: str) -> None:
        if participant_id in self.participants:
            state = self.participants[participant_id]
            state.close()
            del self.participants[participant_id]

    async def transcribe(self, chunk: Chunk) -> None:
        if chunk.participant_id not in self.participants:
            self.add_participant(chunk.participant_id, chunk.language)

        state = self.participants[chunk.participant_id]
        await state.transcribe(chunk)

        if state.has_new_result():
            result = state.get_result()
            await self.websocket.send_json(result.dict())
