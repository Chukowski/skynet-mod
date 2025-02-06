import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse

from skynet import http_client
from skynet.env import app_port, enable_haproxy_agent, enable_metrics, modules
from skynet.haproxy_agent import create_tcpserver
from skynet.logs import get_logger
from skynet.utils import create_app, create_webserver

log = get_logger(__name__)

if not modules:
    log.warning('No modules enabled!')
    sys.exit(1)

log.info(f'Enabled modules: {modules}')
log.info('Using CPU')

@asynccontextmanager
async def lifespan(main_app: FastAPI):
    log.info('Skynet became self aware')

    if 'streaming_whisper' in modules:
        from skynet.modules.stt.streaming_whisper.app import app as streaming_whisper_app
        main_app.mount('/streaming-whisper', streaming_whisper_app)

    if enable_metrics:
        from skynet.metrics import metrics
        main_app.mount('/metrics', metrics)

    yield

app = create_app(lifespan=lifespan)

@app.get('/')
def root():
    return FileResponse('demos/streaming-whisper/index.html')

async def main():
    server = await create_webserver(app, port=app_port)
    
    if enable_haproxy_agent:
        tcpserver = await create_tcpserver()
    
    try:
        await asyncio.gather(
            server.serve(),
            *([] if not enable_haproxy_agent else [tcpserver.serve()])
        )
    finally:
        await http_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
