FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pandas==3.0.1 pyarrow==23.0.1 duckdb==1.5.2 numpy==2.4.2 pyyaml==6.0.3

WORKDIR /workspace
COPY workspace/ /workspace/

# Stage data: download demo, apply corruption, verify against the build-time
# labels copy, then erase BOTH the staging scripts AND the build-time labels
# copy in the same layer so the agent never sees them in the merged view.
COPY build_inputs/labels.csv /tmp/build_labels.csv
RUN python /workspace/stage_data.py \
        --config /workspace/task_config.yaml \
        --output-dir /workspace/data \
        --verify-against /tmp/build_labels.csv \
        --no-duckdb \
    && rm /workspace/stage_data.py /workspace/inject.py /workspace/task_config.yaml \
    && rm /tmp/build_labels.csv

RUN mkdir -p /workspace/submission
