from skynet.env import enable_metrics, modules
from skynet.logs import get_logger
from skynet.modules.monitoring import (
    instrumentator,
    PROMETHEUS_NAMESPACE,
    PROMETHEUS_STREAMING_WHISPER_SUBSYSTEM,
)
from skynet.utils import create_app

log = get_logger(__name__)
metrics = create_app()

if enable_metrics:
    @metrics.get('/healthz')
    def health():
        '''
        Health checking.
        '''
        return {'status': 'ok'}

    if 'streaming_whisper' in modules:
        from skynet.modules.stt.streaming_whisper.app import app as streaming_whisper_app

        instrumentator.instrument(
            streaming_whisper_app,
            prefix=f'{PROMETHEUS_NAMESPACE}_{PROMETHEUS_STREAMING_WHISPER_SUBSYSTEM}'
        )
