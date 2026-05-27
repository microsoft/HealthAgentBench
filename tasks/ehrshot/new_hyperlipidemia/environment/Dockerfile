FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl util-linux unzip \
    && rm -rf /var/lib/apt/lists/*

# Pre-install the standard ML stack so the agent can fit a count+GBM
# baseline (or a FM-embedding-based classifier) without runtime pip.
# ``redivis`` is needed by the bootstrap service to pull the EHRSHOT bundle
# on cache miss; the main service ignores it.
RUN pip install --no-cache-dir \
    numpy==2.1.3 \
    pandas==2.2.3 \
    scipy==1.14.1 \
    scikit-learn==1.5.2 \
    lightgbm==4.5.0 \
    xgboost==2.1.3 \
    pyarrow==18.1.0 \
    redivis==0.20.7

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
# Slicer + scorer baked into the image. Bootstrap runs stage_data.py to
# populate /workspace/data/ AND /tests/test_labels.csv from the downloaded
# bundle. The trial-side verifier imports evaluate.py to compute AUROC.
COPY environment/bootstrap.sh /bootstrap.sh
COPY environment/stage_data.py /opt/ehrshot/stage_data.py
COPY environment/evaluate.py   /opt/ehrshot/evaluate.py
RUN chmod +x /bootstrap.sh \
    && mkdir -p /workspace/submission /workspace/data

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity``. The bootstrap service uses an explicit
# ``command:`` in docker-compose.yaml to run /bootstrap.sh and exit cleanly.
