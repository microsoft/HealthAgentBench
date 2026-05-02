FROM python:3.12-slim

# build-essential + python3-dev are needed for pytrec_eval (C extension).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl util-linux build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytrec_eval==0.5 remotezip==0.12.3 pyyaml==6.0.3 filelock==3.18.0 numpy==2.4.2

# Don't write .pyc files anywhere — keeps the bind-mounted /tests dir
# free of root-owned __pycache__ residue that the host can't delete.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
COPY environment/workspace/ /workspace/
COPY environment/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p /workspace/submission /workspace/data \
    && mv /workspace/topic.txt /workspace/data/topic.txt \
    && mv /workspace/topic_id.txt /workspace/data/topic_id.txt

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
