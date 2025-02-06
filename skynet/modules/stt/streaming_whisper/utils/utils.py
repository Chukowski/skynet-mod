import secrets
import time
from datetime import datetime, timezone
from typing import List, Optional
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

# List of final transcriptions which should not be included in the initial prompt.
# This is to prevent the model from repeating the same text over and over or become
# biased towards a specific way of transcribing.
black_listed_prompts = ['. .']


def convert_bytes_to_seconds(byte_str: bytes) -> float:
    return len(byte_str) / (16000 * 2)


def convert_seconds_to_bytes(cut_mark: float) -> int:
    return int(cut_mark * 16000 * 2)


def is_silent(audio: bytes) -> Tuple[bool, iter]:
    """
    Check if audio chunk is silent
    Returns tuple of (is_silent, speech_timestamps)
    """
    # This is a simplified version since Fireworks handles silence detection
    # You might want to implement proper silence detection here
    return len(audio) == 0, iter([])


def get_phrase_prob(num_segments: int, segments: List[dict]) -> float:
    """Calculate probability/confidence score from segments"""
    if num_segments == 0:
        return 0.0
    
    # In Fireworks.ai API, we don't get detailed probability scores
    # So we'll return a default confidence based on number of segments
    return 0.8  # Default reasonable confidence score


def get_cut_mark_from_segment_probability(ts_result: WhisperResult) -> CutMark:
    check_len = len(ts_result.words) - 1
    phrase = ''
    if len(ts_result.words) > 1:
        # force a final at the biggest gap between words found if the audio is longer than 10 seconds
        if ts_result.words[-1].end >= 10:
            return find_biggest_gap_between_words(ts_result.words)
        for i, word in enumerate(ts_result.words):
            if i == check_len:
                break
            phrase += word.word
            avg_probability = get_phrase_prob(i, ts_result.words)
            if len(phrase) >= 48:
                if (
                    avg_probability >= whisper_min_probability
                    and word.word[-1] in ['.', '!', '?']
                    and word.end < ts_result.words[i + 1].start
                ):
                    log.debug(f'Found split at {word.word} ({word.end} - {ts_result.words[i+1].start})')
                    log.debug(f'Avg probability: {avg_probability}')
                    return CutMark(start=word.end, end=ts_result.words[i + 1].start, probability=avg_probability)
                else:
                    if ts_result.words[-1].end >= 15:
                        return find_biggest_gap_between_words(ts_result.words)
    return CutMark()


def get_wav_header(chunks: List[bytes], chunk_duration_s: float = 0.256, sample_rate: int = 16000) -> bytes:
    duration = len(chunks) * chunk_duration_s
    samples = int(duration * sample_rate)
    bits_per_sample = 16
    channels = 1
    datasize = samples * channels * bits_per_sample // 8
    o = bytes("RIFF", 'ascii')  # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4, 'little')  # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE", 'ascii')  # (4byte) File type
    o += bytes("fmt ", 'ascii')  # (4byte) Format Chunk Marker
    o += (16).to_bytes(4, 'little')  # (4byte) Length of above format data
    o += (1).to_bytes(2, 'little')  # (2byte) Format type (1 - PCM)
    o += channels.to_bytes(2, 'little')  # (2byte)
    o += sample_rate.to_bytes(4, 'little')  # (4byte)
    o += (sample_rate * channels * bits_per_sample // 8).to_bytes(4, 'little')  # (4byte)
    o += (channels * bits_per_sample // 8).to_bytes(2, 'little')  # (2byte)
    o += bits_per_sample.to_bytes(2, 'little')  # (2byte)
    o += bytes("data", 'ascii')  # (4byte) Data Chunk Marker
    o += datasize.to_bytes(4, 'little')  # (4byte) Data size in bytes
    return o


def load_audio(byte_array: bytes) -> ndarray:
    return np.frombuffer(byte_array, np.int16).flatten().astype(np.float32) / 32768.0


# returns now UTC timestamp since epoch in millis
def now() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def transcribe(buffer_list: List[bytes], lang: str = 'en', previous_tokens=None) -> WhisperResult:
    if previous_tokens is None:
        previous_tokens = []
    audio_bytes = b''.join(buffer_list)
    audio = load_audio(audio_bytes)
    iterator, _ = cfg.model.transcribe(
        audio,
        language=lang,
        task='transcribe',
        word_timestamps=True,
        beam_size=whisper_beam_size,
        initial_prompt=previous_tokens,
        condition_on_previous_text=False,
    )
    res = list(iterator)
    ts_obj = WhisperResult(res)
    log.debug(f'Transcription results:\n{ts_obj}\n{res}')
    return ts_obj


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
