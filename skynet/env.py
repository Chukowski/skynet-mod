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

# monitoring
enable_metrics = tobool(os.environ.get('ENABLE_METRICS'))
enable_haproxy_agent = tobool(os.environ.get('ENABLE_HAPROXY_AGENT'))

# auth
bypass_auth = tobool(os.environ.get('BYPASS_AUTHORIZATION'))

# Fireworks.ai settings
fireworks_api_key = os.environ.get('FIREWORKS_API_KEY')
whisper_language = os.environ.get('WHISPER_LANGUAGE', 'es')
