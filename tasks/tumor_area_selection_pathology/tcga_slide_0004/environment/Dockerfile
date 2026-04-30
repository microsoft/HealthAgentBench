FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    wget \
    util-linux \
    jq \
    openslide-tools \
    libopenslide0 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    imagecodecs \
    numpy \
    pillow \
    requests \
    tifffile \
    openslide-python \
    torch \
    torchvision \
    timm>=1.0.3

WORKDIR /workspace

COPY environment/workspace/ /workspace/
COPY environment/task_manifest.json /opt/task_manifest.json
COPY environment/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && mkdir -p /logs/verifier /logs/artifacts /data/cache /data/slide/current

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
