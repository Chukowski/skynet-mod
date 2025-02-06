import os
from typing import Optional
import websockets
import json
import asyncio
from urllib.parse import urlencode

class FireworksStreamingClient:
    def __init__(self, api_key: str, language: Optional[str] = None):
        self.api_key = api_key
        self.language = language
        self.ws = None
        self.base_url = "wss://audio-streaming.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions/streaming"

    async def connect(self):
        params = {
            "response_format": "verbose_json",
        }
        if self.language:
            params["language"] = self.language

        url = f"{self.base_url}?{urlencode(params)}"
        self.ws = await websockets.connect(
            url,
            extra_headers={"Authorization": self.api_key}
        )

    async def send_audio(self, audio_chunk: bytes):
        if not self.ws:
            raise RuntimeError("WebSocket not connected. Call connect() first.")
        await self.ws.send(audio_chunk)

    async def receive_transcription(self):
        if not self.ws:
            raise RuntimeError("WebSocket not connected. Call connect() first.")
        response = await self.ws.recv()
        return json.loads(response)

    async def close(self):
        if self.ws:
            await self.ws.close()
            self.ws = None

# Global client instance
_client: Optional[FireworksStreamingClient] = None

def get_client(language: Optional[str] = None) -> FireworksStreamingClient:
    global _client
    if not _client:
        api_key = os.getenv("FIREWORKS_API_KEY")
        if not api_key:
            raise ValueError("FIREWORKS_API_KEY environment variable not set")
        _client = FireworksStreamingClient(api_key, language)
    return _client
