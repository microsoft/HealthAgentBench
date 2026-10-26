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
    "slide_1.svs|slide_0012.svs|https://api.gdc.cancer.gov/data/dac993ee-b4af-4e94-9b4d-3effe2ff10e0"
    "slide_2.svs|slide_0133.svs|https://api.gdc.cancer.gov/data/076475c7-34c4-4a0a-a3c2-17db9306b77b"
    "slide_3.svs|slide_0080.svs|https://api.gdc.cancer.gov/data/3ac93463-efd7-4291-ab32-a42593030b85"
    "slide_4.svs|slide_0017.svs|https://api.gdc.cancer.gov/data/308aab6a-256e-4c7a-bfcc-e20d379ed6ec"
    "slide_5.svs|slide_0104.svs|https://api.gdc.cancer.gov/data/1bb0465e-63a3-456d-8505-fa57170708a9"
    "slide_6.svs|slide_0094.svs|https://api.gdc.cancer.gov/data/b03e342b-d8e9-4130-9e9b-f5cdf6ab34e6"
    "slide_7.svs|slide_0092.svs|https://api.gdc.cancer.gov/data/57efd582-deba-4c66-a15c-9c5f15a38c11"
    "slide_8.svs|slide_0088.svs|https://api.gdc.cancer.gov/data/caf451b3-430c-4996-bcad-692cf5cef071"
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
