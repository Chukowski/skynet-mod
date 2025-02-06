FROM python:3.11-slim as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

RUN python -m venv .venv && \
    . .venv/bin/activate && \
    pip install -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1001 jitsi && \
    useradd -r -u 1001 -g jitsi jitsi

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY --chown=jitsi:jitsi /skynet /app/skynet/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR ${PYTHONPATH}
RUN chown jitsi:jitsi ${PYTHONPATH}

# Document the exposed port
EXPOSE 8000

# Use the unprivileged user
USER 1001

# Use tini as init
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run Skynet
CMD ["/app/.venv/bin/python", "-m", "skynet.main"]
