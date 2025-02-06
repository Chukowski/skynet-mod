import secrets
import time
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from pydantic import BaseModel
import base64
import uuid

from skynet.logs import get_logger

log = get_logger(__name__)


class WhisperWord(BaseModel):
    probability: float
    word: str
    start: float
    end: float


class WhisperSegment(BaseModel):
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: List


class TranscriptionResponse(BaseModel):
    id: str
    participant_id: str
    ts: int
    text: str
    audio: Optional[str] = None
    type: str = "interim"  # "interim" or "final"
    variance: float = 0.0


class CutMark(BaseModel):
    start: float = 0.0
    end: float = 0.0
    probability: float = 0.0


class WhisperResult:
    text: str
    segments: list[WhisperSegment]
    words: list[WhisperWord]
    confidence: float
    language: str

    def __init__(self, ts_result):
        self.text = ''.join([segment.text for segment in ts_result])
        self.segments = [WhisperSegment.model_validate(segment._asdict()) for segment in ts_result]
        self.words = [WhisperWord.model_validate(word._asdict()) for segment in ts_result for word in segment.words]
        self.confidence = self.get_confidence()

    def __str__(self):
        return (
            f'Text: {self.text}\n'
            + f'Confidence avg: {self.confidence}\n'
            + f'Segments: {self.segments}\n'
            + f'Words: {self.words}'
        )

    def get_confidence(self) -> float:
        if len(self.words) > 0:
            return float(sum(word.probability for word in self.words) / len(self.words))
        return 0.0


LANGUAGES = {
    "en": "english",
    "zh": "chinese",
    "de": "german",
    "es": "spanish",
    "ru": "russian",
    "ko": "korean",
    "fr": "french",
    "ja": "japanese",
    "pt": "portuguese",
    "tr": "turkish",
    "pl": "polish",
    "ca": "catalan",
    "nl": "dutch",
    "ar": "arabic",
    "sv": "swedish",
    "it": "italian",
    "id": "indonesian",
    "hi": "hindi",
    "fi": "finnish",
    "vi": "vietnamese",
    "he": "hebrew",
    "uk": "ukrainian",
    "el": "greek",
    "ms": "malay",
    "cs": "czech",
    "ro": "romanian",
    "da": "danish",
    "hu": "hungarian",
    "ta": "tamil",
    "no": "norwegian",
    "th": "thai",
    "ur": "urdu",
    "hr": "croatian",
    "bg": "bulgarian",
    "lt": "lithuanian",
    "la": "latin",
    "mi": "maori",
    "ml": "malayalam",
    "cy": "welsh",
    "sk": "slovak",
    "te": "telugu",
    "fa": "persian",
    "lv": "latvian",
    "bn": "bengali",
    "sr": "serbian",
    "az": "azerbaijani",
    "sl": "slovenian",
    "kn": "kannada",
    "et": "estonian",
    "mk": "macedonian",
    "br": "breton",
    "eu": "basque",
    "is": "icelandic",
    "hy": "armenian",
    "ne": "nepali",
    "mn": "mongolian",
    "bs": "bosnian",
    "kk": "kazakh",
    "sq": "albanian",
    "sw": "swahili",
    "gl": "galician",
    "mr": "marathi",
    "pa": "punjabi",
    "si": "sinhala",
    "km": "khmer",
    "sn": "shona",
    "yo": "yoruba",
    "so": "somali",
    "af": "afrikaans",
    "oc": "occitan",
    "ka": "georgian",
    "be": "belarusian",
    "tg": "tajik",
    "sd": "sindhi",
    "gu": "gujarati",
    "am": "amharic",
    "yi": "yiddish",
    "lo": "lao",
    "uz": "uzbek",
    "fo": "faroese",
    "ht": "haitian creole",
    "ps": "pashto",
    "tk": "turkmen",
    "nn": "nynorsk",
    "mt": "maltese",
    "sa": "sanskrit",
    "lb": "luxembourgish",
    "my": "myanmar",
    "bo": "tibetan",
    "tl": "tagalog",
    "mg": "malagasy",
    "as": "assamese",
    "tt": "tatar",
    "haw": "hawaiian",
    "ln": "lingala",
    "ha": "hausa",
    "ba": "bashkir",
    "jw": "javanese",
    "su": "sudanese",
}


black_listed_prompts = ['. .']


def convert_bytes_to_seconds(byte_str: bytes) -> float:
    return len(byte_str) / (16000 * 2)


def convert_seconds_to_bytes(cut_mark: float) -> int:
    return int(cut_mark * 16000 * 2)


def get_wav_header(chunks: List[bytes], chunk_duration_s: float = 0.256, sample_rate: int = 16000) -> bytes:
    """Generate WAV header for the given audio chunks"""
    total_samples = int(len(chunks) * chunk_duration_s * sample_rate)
    total_size = total_samples * 2  # 16-bit audio = 2 bytes per sample
    
    header = bytearray()
    # RIFF header
    header.extend(b'RIFF')
    header.extend((total_size + 36).to_bytes(4, 'little'))  # File size - 8
    header.extend(b'WAVE')
    
    # Format chunk
    header.extend(b'fmt ')
    header.extend((16).to_bytes(4, 'little'))  # Chunk size
    header.extend((1).to_bytes(2, 'little'))  # Audio format (1 = PCM)
    header.extend((1).to_bytes(2, 'little'))  # Number of channels
    header.extend(sample_rate.to_bytes(4, 'little'))  # Sample rate
    header.extend((sample_rate * 2).to_bytes(4, 'little'))  # Byte rate
    header.extend((2).to_bytes(2, 'little'))  # Block align
    header.extend((16).to_bytes(2, 'little'))  # Bits per sample
    
    # Data chunk
    header.extend(b'data')
    header.extend(total_size.to_bytes(4, 'little'))
    
    return header


def now() -> int:
    """Returns now UTC timestamp since epoch in millis"""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_lang(lang: str, short=True) -> str:
    if len(lang) == 2 and short:
        return lang.lower().strip()
    if '-' in lang and short:
        return lang.split('-')[0].strip()
    if not short and '-' in lang:
        split_key = lang.split('-')[0]
        return LANGUAGES.get(split_key, 'english').lower().strip()
    return lang.lower().strip()


class Uuid7:
    def get(self) -> uuid.UUID:
        return uuid.uuid4()  # Using uuid4 for simplicity
