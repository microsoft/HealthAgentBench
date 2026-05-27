"""Build tiny synthetic CSVs in this directory for offline tests.

Run:
    uv run python tests/fixtures/ehr_data_quality/build_fixtures.py

Output:
    tests/fixtures/ehr_data_quality/raw/{hosp,icu}/<table>.csv.gz
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent / "raw"
HOSP = OUT / "hosp"
ICU = OUT / "icu"
HOSP.mkdir(parents=True, exist_ok=True)
ICU.mkdir(parents=True, exist_ok=True)


def write(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, compression="gzip")


# Twenty patients keeps the offline fixture realistic enough that the in-scope
# subset for any task is non-empty.
patients = pd.DataFrame(
    [
        {
            "subject_id": sid,
            # Even subject_ids → F (matches the female-marker drugs added below).
            "gender": "F" if sid % 2 == 0 else "M",
            "anchor_age": 50 + (sid % 30),
            "anchor_year": 2180,
            "anchor_year_group": "2014 - 2016",
            "dod": "",
        }
        for sid in range(10000, 10020)
    ]
)
write(patients, HOSP / "patients.csv.gz")

admissions = pd.DataFrame(
    [
        {
            "subject_id": sid,
            "hadm_id": sid * 10,
            "admittime": "2180-01-01 10:00:00",
            "dischtime": "2180-01-05 10:00:00",
            "deathtime": "",
            "admission_type": "URGENT",
            "admission_location": "EMERGENCY ROOM",
            "discharge_location": "HOME",
            "insurance": "Other",
            "language": "ENGLISH",
            "marital_status": "SINGLE",
            "race": "WHITE",
            "edregtime": "",
            "edouttime": "",
            "hospital_expire_flag": 0,
        }
        for sid in range(10000, 10020)
    ]
)
write(admissions, HOSP / "admissions.csv.gz")

lab_rows = []
for i, sid in enumerate(range(10000, 10020)):
    for itemid, base in [(50912, 1.0), (50931, 100.0), (50971, 4.0), (50983, 140.0)]:
        lab_rows.append(
            {
                "labevent_id": len(lab_rows) + 1,
                "subject_id": sid,
                "hadm_id": sid * 10,
                "itemid": itemid,
                "charttime": "2180-01-01 12:00:00",
                "storetime": "2180-01-01 13:00:00",
                "value": str(base + 0.1 * i),
                "valuenum": base + 0.1 * i,
                "valueuom": "mg/dL",
                "ref_range_lower": 0.5,
                "ref_range_upper": 1.5,
                "flag": "",
                "priority": "ROUTINE",
                "comments": "",
            }
        )
write(pd.DataFrame(lab_rows), HOSP / "labevents.csv.gz")

def _rx(i, sid, drug, dose):
    return {
        "subject_id": sid, "hadm_id": sid * 10, "pharmacy_id": i,
        "poe_id": f"poe_{i}", "poe_seq": i,
        "starttime": "2180-01-02 08:00:00", "stoptime": "2180-01-02 20:00:00",
        "drug_type": "MAIN", "drug": drug,
        "formulary_drug_cd": drug[:8].upper(), "gsn": f"{i:06d}",
        "ndc": f"00904{i:06d}", "prod_strength": f"{dose} Tablet",
        "form_rx": "TAB", "dose_val_rx": str(dose), "dose_unit_rx": "mg",
        "form_val_disp": "1", "form_unit_disp": "TAB",
        "doses_per_24_hrs": "", "route": "PO",
    }


# Mostly Acetaminophen + a handful of demographic-marker drugs so the
# offline fixture exercises demographic_conflict.
rx_rows = []
for i, sid in enumerate(range(10000, 10020)):
    rx_rows.append(_rx(i, sid, "Acetaminophen", 500))
# Female patients (10000, 10002, ...) on Tamoxifen — will be flipped to M.
rx_rows.append(_rx(100, 10000, "Tamoxifen Citrate", 20))
rx_rows.append(_rx(101, 10002, "Estradiol", 1))
# Age >= 50 patients on Donepezil — anchor_age will be rewritten to 5.
rx_rows.append(_rx(102, 10004, "Donepezil", 10))
prescriptions = pd.DataFrame(rx_rows)
write(prescriptions, HOSP / "prescriptions.csv.gz")

d_labitems = pd.DataFrame(
    [
        {
            "itemid": itemid,
            "label": label,
            "fluid": "Blood",
            "category": "Chemistry",
        }
        for itemid, label in [
            (50912, "Creatinine"),
            (50931, "Glucose"),
            (50971, "Potassium"),
            (50983, "Sodium"),
        ]
    ]
)
write(d_labitems, HOSP / "d_labitems.csv.gz")

icustays = pd.DataFrame(
    [
        {
            "subject_id": sid,
            "hadm_id": sid * 10,
            "stay_id": sid * 100,
            "first_careunit": "MICU",
            "last_careunit": "MICU",
            "intime": "2180-01-02 14:00:00",
            "outtime": "2180-01-04 09:00:00",
            "los": 1.79,
        }
        for sid in range(10000, 10005)
    ]
)
write(icustays, ICU / "icustays.csv.gz")

chart_rows = []
for i, sid in enumerate(range(10000, 10020)):
    for itemid, base in [(220045, 80), (220179, 120), (220180, 80), (220277, 98), (223761, 98.6)]:
        chart_rows.append(
            {
                "subject_id": sid,
                "hadm_id": sid * 10,
                "stay_id": sid * 100,
                "caregiver_id": 1,
                "charttime": "2180-01-02 16:00:00",
                "storetime": "2180-01-02 17:00:00",
                "itemid": itemid,
                "value": base + 0.5 * i,
                "valuenum": base + 0.5 * i,
                "valueuom": "bpm",
                "warning": 0,
            }
        )
write(pd.DataFrame(chart_rows), ICU / "chartevents.csv.gz")

d_items = pd.DataFrame(
    [
        {"itemid": itemid, "label": label, "abbreviation": label, "linksto": "chartevents",
         "category": "Routine Vital Signs", "unitname": "bpm", "param_type": "Numeric",
         "lownormalvalue": "", "highnormalvalue": ""}
        for itemid, label in [
            (220045, "Heart Rate"),
            (220179, "Non Invasive Blood Pressure systolic"),
            (220180, "Non Invasive Blood Pressure diastolic"),
            (220277, "O2 saturation pulseoxymetry"),
            (223761, "Temperature Fahrenheit"),
        ]
    ]
)
write(d_items, ICU / "d_items.csv.gz")

print("Fixtures written:")
for p in sorted(OUT.rglob("*.csv.gz")):
    print(" ", p.relative_to(OUT.parent))
