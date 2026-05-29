from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlopen

DEMO_BASE_URL = "https://physionet.org/files/mimic-iv-demo/2.2"
COMMON_BASE_URL = "https://raw.githubusercontent.com/MIT-LCP/mimic-code/v2.4.0/mimic-iv/concepts/concept_map"
FILES = [
  "LICENSE.txt",
  "README.txt",
  "SHA256SUMS.txt",
  "d_labitems_to_loinc.csv",
  "demo_subject_id.csv",
  "hosp/admissions.csv.gz",
  "hosp/d_hcpcs.csv.gz",
  "hosp/d_icd_diagnoses.csv.gz",
  "hosp/d_icd_procedures.csv.gz",
  "hosp/d_labitems.csv.gz",
  "hosp/diagnoses_icd.csv.gz",
  "hosp/drgcodes.csv.gz",
  "hosp/emar.csv.gz",
  "hosp/emar_detail.csv.gz",
  "hosp/hcpcsevents.csv.gz",
  "hosp/labevents.csv.gz",
  "hosp/microbiologyevents.csv.gz",
  "hosp/omr.csv.gz",
  "hosp/patients.csv.gz",
  "hosp/pharmacy.csv.gz",
  "hosp/poe.csv.gz",
  "hosp/poe_detail.csv.gz",
  "hosp/prescriptions.csv.gz",
  "hosp/procedures_icd.csv.gz",
  "hosp/provider.csv.gz",
  "hosp/services.csv.gz",
  "hosp/transfers.csv.gz",
  "icu/caregiver.csv.gz",
  "icu/chartevents.csv.gz",
  "icu/d_items.csv.gz",
  "icu/datetimeevents.csv.gz",
  "icu/icustays.csv.gz",
  "icu/ingredientevents.csv.gz",
  "icu/inputevents.csv.gz",
  "icu/outputevents.csv.gz",
  "icu/procedureevents.csv.gz",
  "inputevents_to_rxnorm.csv",
  "lab_itemid_to_loinc.csv",
  "meas_chartevents_main.csv",
  "meas_chartevents_value.csv",
  "numerics-summary.csv",
  "outputevents_to_loinc.csv",
  "proc_datetimeevents.csv",
  "proc_itemid.csv",
  "waveforms-summary.csv"
]
COMMON_NAMES = {
    "d_labitems_to_loinc.csv",
    "inputevents_to_rxnorm.csv",
    "lab_itemid_to_loinc.csv",
    "meas_chartevents_main.csv",
    "meas_chartevents_value.csv",
    "numerics-summary.csv",
    "outputevents_to_loinc.csv",
    "proc_datetimeevents.csv",
    "proc_itemid.csv",
    "waveforms-summary.csv",
}


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as resp:
        dest.write_bytes(resp.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    for rel in FILES:
        if rel in COMMON_NAMES:
            url = f"{COMMON_BASE_URL}/{rel}"
        else:
            url = f"{DEMO_BASE_URL}/{rel}"
        download(url, args.output_dir / rel)


if __name__ == "__main__":
    main()
