FROM python:3.11-bookworm

# Docker automatically provides TARGETARCH (amd64, arm64, etc.) for multi-platform builds
ARG TARGETARCH
ARG MEMTIER_VERSION=2.1.1

ENV FLASK_APP app.py
ENV APP_SETTINGS settings.cfg
ENV NO_URL_QUOTING True

# Install memtier_benchmark from GitHub releases
# Downloads the appropriate .deb file based on target architecture
# Note: Version 2.1.1 is not available in the Redis APT repository, only on GitHub releases
RUN curl -fsSL -o /tmp/memtier-benchmark.deb \
        "https://github.com/RedisLabs/memtier_benchmark/releases/download/${MEMTIER_VERSION}/memtier-benchmark_${MEMTIER_VERSION}.bookworm_${TARGETARCH}.deb" && \
    apt-get update && \
    apt-get install -y --no-install-recommends /tmp/memtier-benchmark.deb && \
    rm /tmp/memtier-benchmark.deb && \
    rm -rf /var/lib/apt/lists/* && \
    memtier_benchmark --version

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD python -m flask run -p 8080 -h 0.0.0.0
