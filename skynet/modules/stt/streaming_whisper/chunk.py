from dataclasses import dataclass
import struct
import numpy as np
from skynet.modules.stt.streaming_whisper.utils import utils
from skynet.logs import get_logger

log = get_logger(__name__)

@dataclass
class Chunk:
    raw: bytes
    timestamp: int
    duration: float
    size: int
    silent: bool
    speech_timestamps: iter
    participant_id: str
    language: str

    def __init__(self, chunk: bytes, chunk_timestamp: int):
        self._extract(chunk)
        self.timestamp = chunk_timestamp
        self.duration = utils.convert_bytes_to_seconds(self.raw)
        self.size = len(self.raw)
        self.silent, self.speech_timestamps = utils.is_silent(self.raw)

    def _extract(self, chunk: bytes):
        """Extract participant ID, language and audio data from the chunk"""
        try:
            # First 36 bytes contain metadata (UUID)
            self.participant_id = chunk[:36].decode('utf-8')
            # Next 2 bytes contain language code length
            lang_len = struct.unpack('!H', chunk[36:38])[0]
            # Extract language code
            self.language = chunk[38:38+lang_len].decode('utf-8')
            # Rest is audio data
            audio_data = chunk[38+lang_len:]
            
            # Convert audio to 16kHz mono PCM if needed
            # Assuming input is float32 [-1.0, 1.0]
            float_audio = np.frombuffer(audio_data, dtype=np.float32)
            
            # Convert to 16-bit PCM
            int16_audio = (float_audio * 32767).astype(np.int16)
            
            # Convert to bytes
            self.raw = int16_audio.tobytes()
            
        except Exception as e:
            # Fallback to default values if parsing fails
            self.participant_id = "default"
            self.language = "en"
            self.raw = chunk
