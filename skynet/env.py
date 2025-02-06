import os
import sys
import uuid

app_uuid = str(uuid.uuid4())

# utilities
def tobool(val: str | None):
    if val is None:
        return False
    val = val.lower().strip()
    if val in ['y', 'yes', 'true', '1']:
        return True
    return False

# general
app_port = int(os.getenv('APP_PORT', '8001'))
log_level = os.environ.get('LOG_LEVEL', 'DEBUG').strip().upper()
supported_modules = {'streaming_whisper'}
enabled_modules = set(os.environ.get('ENABLED_MODULES', 'streaming_whisper').split(','))
modules = supported_modules.intersection(enabled_modules)

# WebSocket settings
ws_max_size_bytes = int(os.environ.get('WS_MAX_SIZE_BYTES', 1000000))
ws_max_queue_size = int(os.environ.get('WS_MAX_QUEUE_SIZE', 3000))
ws_max_ping_interval = int(os.environ.get('WS_MAX_PING_INTERVAL', 30))
ws_max_ping_timeout = int(os.environ.get('WS_MAX_PING_TIMEOUT', 30))
whisper_max_connections = int(os.environ.get('WHISPER_MAX_CONNECTIONS', 10))
whisper_flush_interval = int(os.environ.get('WHISPER_FLUSH_BUFFER_INTERVAL', 2000))

# monitoring
enable_metrics = tobool(os.environ.get('ENABLE_METRICS'))
enable_haproxy_agent = tobool(os.environ.get('ENABLE_HAPROXY_AGENT'))

# auth
bypass_auth = tobool(os.environ.get('BYPASS_AUTHORIZATION'))
asap_pub_keys_url = os.environ.get('ASAP_PUB_KEYS_URL', '')
asap_pub_keys_folder = os.environ.get('ASAP_PUB_KEYS_FOLDER', '')
asap_pub_keys_fallback_folder = os.environ.get('ASAP_PUB_KEYS_FALLBACK_FOLDER', '')
asap_pub_keys_max_cache_size = int(os.environ.get('ASAP_PUB_KEYS_MAX_CACHE_SIZE', '1000'))
asap_pub_keys_auds = os.environ.get('ASAP_PUB_KEYS_AUDS', '').split(',')

# Fireworks.ai settings
fireworks_api_key = os.environ.get('FIREWORKS_API_KEY')
whisper_language = os.environ.get('WHISPER_LANGUAGE', 'es')
