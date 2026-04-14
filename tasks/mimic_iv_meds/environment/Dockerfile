FROM python:3.11-slim

RUN apt-get update     && apt-get install -y --no-install-recommends bash ca-certificates curl git     && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.9.26 pyarrow==23.0.1 pyyaml==6.0.3

WORKDIR /workspace
COPY workspace/ /workspace/
ENV PYTHONPATH=/workspace/runtime_patch

RUN git clone https://github.com/Medical-Event-Data-Standard/MIMIC_IV_MEDS.git /workspace/MIMIC_IV_MEDS     && cd /workspace/MIMIC_IV_MEDS     && git checkout 9699e0865b050325459b11f3c4e226a9dbe5b496     && test "$(git rev-parse HEAD)" = "9699e0865b050325459b11f3c4e226a9dbe5b496"

RUN python /workspace/scripts/stage_demo_data.py --output-dir /workspace/staged_demo/raw_input
