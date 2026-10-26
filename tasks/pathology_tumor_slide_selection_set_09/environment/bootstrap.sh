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
    "slide_1.svs|slide_0017.svs|https://api.gdc.cancer.gov/data/308aab6a-256e-4c7a-bfcc-e20d379ed6ec"
    "slide_2.svs|slide_0086.svs|https://api.gdc.cancer.gov/data/a2be897c-18e0-498c-a417-93fcd13713c6"
    "slide_3.svs|slide_0107.svs|https://api.gdc.cancer.gov/data/6a9bd5b9-efdd-4b32-9299-85544cdbb8b7"
    "slide_4.svs|slide_0085.svs|https://api.gdc.cancer.gov/data/8f5f009b-d403-488d-aa6b-9d1d34e95df5"
    "slide_5.svs|slide_0100.svs|https://api.gdc.cancer.gov/data/7bf22346-d3ab-4ff8-8568-541cbec1470c"
    "slide_6.svs|slide_0016.svs|https://api.gdc.cancer.gov/data/24f48355-52b7-4bfa-8d6f-67fe7c5bebac"
    "slide_7.svs|slide_0148.svs|https://api.gdc.cancer.gov/data/318adffd-5a63-4963-8fbe-51d17f3842ac"
    "slide_8.svs|slide_0113.svs|https://api.gdc.cancer.gov/data/ecc6354f-75a8-47b5-87e8-71bcce237bdf"
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
