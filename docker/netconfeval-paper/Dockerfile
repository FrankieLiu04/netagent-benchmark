FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/workspace:/workspace/research/netconfeval

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY docker/netconfeval-paper/requirements.txt /tmp/netconfeval-paper-requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/netconfeval-paper-requirements.txt

CMD ["/bin/bash"]
