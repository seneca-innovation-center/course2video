FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg fonts-dejavu-core curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
ARG EXTRAS=math,piper
RUN pip install --no-cache-dir -e ".[${EXTRAS}]"

COPY configs ./configs
COPY scripts ./scripts
COPY examples ./examples
COPY schemas ./schemas
RUN ./scripts/download_models.sh /app/models/piper

ENTRYPOINT ["course2video"]
CMD ["--help"]
