FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    numpy==2.5.1 \
    pandas==2.3.3 \
    scipy==1.18.0 \
    scikit-learn==1.9.0 \
    scikit-survival==0.28.0 \
    lifelines==0.30.3 \
    pyarrow==25.0.0

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

RUN mkdir -p /workspace/data /workspace/submission

# Harbor keeps the main service alive and invokes the verifier separately.
