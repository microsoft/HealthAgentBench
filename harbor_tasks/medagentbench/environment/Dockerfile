FROM python:3.12-slim

RUN apt-get update             && apt-get install -y --no-install-recommends bash curl jq             && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY workspace/ /workspace/
RUN chmod +x /workspace/scripts/*.sh
