FROM python:3.12-slim

# Pre-install packages Harbor bootstraps for the agent runtime, plus bash/jq.
# wget + util-linux (flock) are used by entrypoint.sh to bootstrap missing
# MIMIC-CXR assets from PhysioNet on first run of any task container.
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    wget \
    util-linux \
    jq \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# CheXbert dependencies for per-trial pathology labeling inside
# verify_meta_task.py. Pinned to versions compatible with f1chexbert:
#   - transformers<5: BertTokenizer.encode_plus was removed in 5.x
#   - scikit-learn: any 1.x is fine (we only call stable APIs)
# The CheXbert BERT weights (~440 MB) are pre-fetched at build time so task
# containers don't hit HuggingFace on every cold start.
RUN pip install --no-cache-dir \
    'torch==2.4.1' \
    'transformers<5' \
    'scikit-learn>=1.3,<1.8' \
    'f1chexbert' \
    'huggingface_hub' \
    'appdirs'
RUN python -c "\
from huggingface_hub import hf_hub_download; \
from appdirs import user_cache_dir; \
import os, shutil; \
cache = user_cache_dir('chexbert'); os.makedirs(cache, exist_ok=True); \
src = hf_hub_download(repo_id='StanfordAIMI/RRG_scorers', filename='chexbert.pth', cache_dir=cache); \
dst = os.path.join(cache, 'chexbert.pth'); \
(os.symlink(src, dst) if not os.path.exists(dst) else None)"

WORKDIR /workspace

COPY environment/workspace/ /workspace/

# Manifest + entrypoint that materialize /data/patient/ at runtime
COPY environment/task_manifest.json /opt/task_manifest.json
COPY environment/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mkdir -p /logs/verifier /data/patient

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
