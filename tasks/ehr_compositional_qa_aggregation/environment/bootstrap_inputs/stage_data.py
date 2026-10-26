"""Build a raw MIMIC-IV-demo DuckDB; never stage labels or derived scores."""

from __future__ import annotations

import argparse
import io
import logging
import urllib.request
import zipfile
from pathlib import Path

import duckdb

MIMIC_IV_DEMO_URL = (
    "https://physionet.org/static/published-projects/mimic-iv-demo/"
    "mimic-iv-demo-2.2.zip"
)

DEFAULT_DEMO_DIR = Path("/tmp/mimic-iv-demo")

logger = logging.getLogger("stage_data")


def download_demo(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading MIMIC-IV-demo from %s", MIMIC_IV_DEMO_URL)
    with urllib.request.urlopen(MIMIC_IV_DEMO_URL) as resp:
        data = resp.read()
    logger.info("Downloaded %.1f MB; extracting", len(data) / 1e6)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(target_dir)
    candidates = [p for p in target_dir.iterdir() if p.is_dir() and p.name.startswith("mimic-iv")]
    if len(candidates) != 1:
        raise RuntimeError(f"Unexpected demo layout under {target_dir}: {candidates!r}")
    return candidates[0]


def load_raw_csvs(con: duckdb.DuckDBPyConnection, demo_root: Path) -> None:
    for area in ("hosp", "icu"):
        area_dir = demo_root / area
        if not area_dir.exists():
            raise RuntimeError(f"Demo missing {area_dir}")
        for csv_path in sorted(area_dir.glob("*.csv*")):
            table = csv_path.name.split(".")[0]
            schema = f"mimiciv_{area}"
            logger.info("Loading %s.%s", schema, table)
            con.execute(
                f"CREATE TABLE {schema}.{table} AS "
                f"SELECT * FROM read_csv_auto(?, all_varchar=false, sample_size=-1)",
                [str(csv_path)],
            )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-db", type=Path, required=True)
    p.add_argument("--demo-dir", type=Path, default=DEFAULT_DEMO_DIR)
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")

    args.output_db.parent.mkdir(parents=True, exist_ok=True)
    if args.output_db.exists():
        args.output_db.unlink()

    demo_root = download_demo(args.demo_dir)

    con = duckdb.connect(str(args.output_db))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS mimiciv_hosp")
        con.execute("CREATE SCHEMA IF NOT EXISTS mimiciv_icu")
        load_raw_csvs(con, demo_root)
    finally:
        con.close()

    logger.info("Done.")


if __name__ == "__main__":
    main()
