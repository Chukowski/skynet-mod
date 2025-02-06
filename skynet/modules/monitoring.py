from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator, metrics

PROMETHEUS_NAMESPACE = 'Skynet'
PROMETHEUS_STREAMING_WHISPER_SUBSYSTEM = 'Streaming_Whisper'

CONNECTIONS_METRIC = Gauge(
    'LiveWsConnections',
    documentation='Number of active WS connections',
    namespace=PROMETHEUS_NAMESPACE,
    subsystem=PROMETHEUS_STREAMING_WHISPER_SUBSYSTEM,
)

TRANSCRIBE_GRACEFUL_SHUTDOWN = Gauge(
    'LiveWsGracefulShutdown',
    documentation='Indicates if the transcriber is in the process of shutting down gracefully',
    namespace=PROMETHEUS_NAMESPACE,
    subsystem=PROMETHEUS_STREAMING_WHISPER_SUBSYSTEM,
)

TRANSCRIBE_STRESS_LEVEL_METRIC = Gauge(
    'stress_level',
    documentation='Whisper stress level',
    namespace=PROMETHEUS_NAMESPACE,
    subsystem=PROMETHEUS_STREAMING_WHISPER_SUBSYSTEM,
)

TRANSCRIBE_CONNECTIONS_COUNTER = Counter(
    'LiveWsConnectionsCounter',
    documentation='Number of active WS connections',
    namespace=PROMETHEUS_NAMESPACE,
    subsystem=PROMETHEUS_STREAMING_WHISPER_SUBSYSTEM,
)

TRANSCRIBE_DURATION_METRIC = Histogram(
    'WhisperTranscriptionDuration',
    documentation='Measures the duration of the transcription process in seconds',
    namespace=PROMETHEUS_NAMESPACE,
    subsystem=PROMETHEUS_STREAMING_WHISPER_SUBSYSTEM,
    buckets=[x / 10.0 for x in range(1, 31)],
)

instrumentator = Instrumentator(
    excluded_handlers=["/healthz", "/metrics"],
)
