FROM python:3.12-slim

# bash + flock for the bootstrap script; curl/wget for the MIMIC-IV demo
# download that stage_data.py performs on cache miss.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       bash ca-certificates curl wget util-linux \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pandas==3.0.1 pyarrow==23.0.1 duckdb==1.5.2 numpy==2.4.2 pyyaml==6.0.3

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
# Compose's build context is the parent (task root), so the path is
# environment/workspace/ rather than workspace/. Match xray_report_gen.
COPY environment/workspace/ /workspace/
RUN mkdir -p /workspace/data /workspace/submission /logs/verifier

# No ENTRYPOINT / CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity`` so the container stays alive for the agent
# + verifier. The bootstrap service uses an explicit ``command:`` in
# docker-compose.yaml to run /bootstrap.sh (bind-mounted) and exit.
