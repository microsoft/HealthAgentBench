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
    "slide_1.svs|slide_0095.svs|https://api.gdc.cancer.gov/data/7abbbc7e-51de-40d9-a695-8b6420bdf383"
    "slide_2.svs|slide_0011.svs|https://api.gdc.cancer.gov/data/67ddde08-cd79-42ac-a2a6-1840859470e4"
    "slide_3.svs|slide_0091.svs|https://api.gdc.cancer.gov/data/cacb48c3-2ad5-439f-ae40-8556d010c08f"
    "slide_4.svs|slide_0087.svs|https://api.gdc.cancer.gov/data/5ddb7ceb-b6a8-4e9b-9fdb-21a863b629ae"
    "slide_5.svs|slide_0081.svs|https://api.gdc.cancer.gov/data/0f3a8842-60a3-48d4-941a-b22ec08f1b32"
    "slide_6.svs|slide_0015.svs|https://api.gdc.cancer.gov/data/6b9207c2-ede7-48ab-97fb-466cf93bbb2b"
    "slide_7.svs|slide_0007.svs|https://api.gdc.cancer.gov/data/b0b7de0c-f12e-448a-aa27-7c9377058d93"
    "slide_8.svs|slide_0050.svs|https://api.gdc.cancer.gov/data/52f76ac4-fd51-4095-8399-4bdfde3361b3"
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
