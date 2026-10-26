#!/bin/bash
# One-shot bootstrap container. Compose starts this service, waits for it to
# exit cleanly, and only then brings main up (depends_on:
# condition: service_completed_successfully).
#
# It fetches this task's slides from upstream into a shared cross-run cache and
# stages them under opaque names into the shared volume that main reads. The
# download URLs and the opaque-name -> source mapping live ONLY in this file,
# which is bind-mounted into the bootstrap service - never baked into the
# image - so the agent can never read them.
set -euo pipefail

# staged name | cache key | download URL
SLIDES=(
    "slide_1.svs|slide_0010.svs|https://api.gdc.cancer.gov/data/1d31d57b-0807-4c39-8d20-6dbae2596348"
    "slide_2.svs|slide_0009.svs|https://api.gdc.cancer.gov/data/0d631254-63db-4e6a-8407-cd6ea423d0e6"
    "slide_3.svs|slide_0082.svs|https://api.gdc.cancer.gov/data/5c5a8034-568c-4af9-ae41-6cc000e4f846"
    "slide_4.svs|slide_0003.svs|https://api.gdc.cancer.gov/data/fcdc7c48-6d3d-4ca8-a0f8-88373ffc2173"
    "slide_5.svs|slide_0099.svs|https://api.gdc.cancer.gov/data/0e83c4b2-8adc-4ada-93b3-e3be63d4c641"
    "slide_6.svs|slide_0001.svs|https://api.gdc.cancer.gov/data/c1831a9f-11ed-44a4-98c2-779a7b61ec46"
    "slide_7.svs|slide_0185.svs|https://api.gdc.cancer.gov/data/c3389c85-7f23-4aaf-871d-b69508f8cfd3"
    "slide_8.svs|slide_0084.svs|https://api.gdc.cancer.gov/data/b37ed849-879b-421c-89a6-39ccfe1c1074"
)

CACHE=/data/_cache
GLOBAL_LOCK="$CACHE/.bootstrap.lock"
DEST_DIR=/data/slides

mkdir -p "$CACHE" "$DEST_DIR"

for row in "${SLIDES[@]}"; do
    IFS='|' read -r STAGED CACHE_KEY URL <<< "$row"
    SRC="$CACHE/$CACHE_KEY"
    # Serialize cold downloads across concurrent task containers sharing the cache.
    exec 9>"$GLOBAL_LOCK"
    flock 9
    if [ ! -s "$SRC" ]; then
        echo "[bootstrap] downloading $STAGED ..."
        ok=0
        for attempt in 1 2 3 4 5 6; do
            rm -f "$SRC.part"
            if curl -fSL --retry 3 --retry-all-errors --connect-timeout 30 \
                    --speed-time 60 --speed-limit 1024 -o "$SRC.part" "$URL"; then
                ok=1
                break
            fi
            echo "[bootstrap] download failed (attempt $attempt), retrying in 30s ..." >&2
            sleep 30
        done
        if [ "$ok" -ne 1 ]; then
            echo "[bootstrap] giving up on $STAGED" >&2
            exit 1
        fi
        mv "$SRC.part" "$SRC"
    fi
    flock -u 9
    cp "$SRC" "$DEST_DIR/$STAGED"
    # Scrub source identifiers from the staged copy. TCGA barcodes embedded in
    # the Aperio ImageDescription (Filename/Title) encode the sample type
    # (01 = primary tumor, 06 = metastatic, 11 = solid tissue normal), i.e. the
    # hidden label. Overwrite every occurrence in place with a same-length
    # placeholder so the TIFF structure stays valid.
    python3 - "$DEST_DIR/$STAGED" <<'PY'
import mmap, re, sys
path = sys.argv[1]
pattern = re.compile(rb"TCGA-[A-Za-z0-9]{2}-[A-Za-z0-9]{4}[A-Za-z0-9-]*")
with open(path, "r+b") as fh:
    mm = mmap.mmap(fh.fileno(), 0)
    n = 0
    for m in pattern.finditer(mm):
        start, end = m.span()
        mm[start:end] = b"X" * (end - start)
        n += 1
    mm.flush()
    mm.close()
print(f"[bootstrap] scrubbed {n} identifier(s) from {path}")
PY
done

echo "[bootstrap] staged ${#SLIDES[@]} slides - main can start"
