# ehr_data_quality — Injected Error Review
Every cluster across all four sub-tasks. One row per cluster (the *anchor* — the actual injected row; evidence rows are summarized by the `Rows` count). The agent only needs to flag one row per cluster to count as caught.

**Flags** based on audit verdicts:
- 🟢 (unflagged) — **unambiguous**: any reasonable EHR analyst would flag this row.
- 🟡 ⚠️ — **defensible but debatable**: an analyst might call it suspicious but not certainly wrong.
- 🔴 🚩 — **false-positive risk**: agent could legitimately miss it (e.g., bedside vs. lab disagreement at real-world variance levels, or reference-range overwrites indistinguishable from institutional variation).

Mark the `Review` checkbox after spot-checking each cluster.

---
## task_combined

**60 clusters** (_788 labeled rows total, including evidence_)


### demographic_conflict


#### `age_via_patients_change` — 🟢 unambiguous

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DEMO\|age_change\|ed8f5279257d4026` | `patients` | `ed8f5279257d4026` | `anchor_age` | 87.0 | 5.0 | 1 prescription(s) Donepezil (Alzheimer's medication, geriatric-only) — clinically impossible for the corrupted age of 5.0. | medium | 2 |  | ☐ |

#### `gender_via_patients_flip` — 🟢 unambiguous

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DEMO\|patients_flip\|ae5ca58c0c61aa20` | `patients` | `ae5ca58c0c61aa20` | `gender` | F | M | 79 of this patient's lab rows (e.g. Creatinine (50912), Hematocrit (51221), Hemoglobin (51222)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`F`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = M` is inconsistent with those reference ranges. | medium | 80 |  | ☐ |
| `DEMO\|patients_flip\|354541523959b259` | `patients` | `354541523959b259` | `gender` | M | F | 174 of this patient's lab rows (e.g. Hemoglobin (51222), Hematocrit (51221), Creatinine (50912)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`M`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = F` is inconsistent with those reference ranges. | medium | 175 |  | ☐ |
| `DEMO\|patients_flip\|ccb4788d5cc49515` | `patients` | `ccb4788d5cc49515` | `gender` | F | M | 37 of this patient's lab rows (e.g. Hemoglobin (51222), Hematocrit (51221), Creatinine (50912)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`F`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = M` is inconsistent with those reference ranges. | medium | 38 |  | ☐ |
| `DEMO\|patients_flip\|08d59a72ce3648d4` | `patients` | `08d59a72ce3648d4` | `gender` | F | M | 65 of this patient's lab rows (e.g. Hemoglobin (51222), Hematocrit (51221), Creatinine (50912)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`F`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = M` is inconsistent with those reference ranges. | medium | 66 |  | ☐ |
| `DEMO\|patients_flip\|72b07858700ddcb2` | `patients` | `72b07858700ddcb2` | `gender` | F | M | 37 of this patient's lab rows (e.g. Hemoglobin (51222), Hematocrit (51221), Creatinine (50912)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`F`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = M` is inconsistent with those reference ranges. | medium | 38 |  | ☐ |

#### `gender_via_prescription_swap` — 🟢 unambiguous

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DEMO\|rx_swap\|ebc226e5a75419ab` | `prescriptions` | `ebc226e5a75419ab` | `drug` | Metoprolol Tartrate | Levonorgestrel | Swapped-in drug Levonorgestrel (oral contraceptive, female-only) contradicts `patients.gender = M`; 23 of this patient's lab rows (e.g. Creatinine (50912), Hemoglobin (51222), Hematocrit (51221)) carry sex-specific `ref_range` bands consistent with the patient's true gender, contradicting the swapped-in marker drug; `patients.gender = M` for this patient. | medium | 25 |  | ☐ |
| `DEMO\|rx_swap\|88579575ee0c94e9` | `prescriptions` | `88579575ee0c94e9` | `drug` | SW | Vardenafil | Swapped-in drug Vardenafil (erectile dysfunction, male-only) contradicts `patients.gender = F`; 47 of this patient's lab rows (e.g. Creatinine (50912), Hematocrit (51221), Hemoglobin (51222)) carry sex-specific `ref_range` bands consistent with the patient's true gender, contradicting the swapped-in marker drug; `patients.gender = F` for this patient. | medium | 49 |  | ☐ |

### impossible_value


#### `range_extreme` — 🟢 unambiguous

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `labevents\|70868fd7a76cc22f` | `labevents` | `70868fd7a76cc22f` | `valuenum` | 0.6 | 718.3 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `labevents\|7284eb6c7661806e` | `labevents` | `7284eb6c7661806e` | `valuenum` | 140.0 | 593.2 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `labevents\|1a5359393eeeea63` | `labevents` | `1a5359393eeeea63` | `valuenum` | 84.0 | 8041.5 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `chartevents\|539cf4bd3fa13588` | `chartevents` | `539cf4bd3fa13588` | `valuenum` | 105.0 | 849.7 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `chartevents\|2cd4f16c2ed8cd37` | `chartevents` | `2cd4f16c2ed8cd37` | `valuenum` | 92.0 | 156.9 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `chartevents\|2ab7b8916f641b0a` | `chartevents` | `2ab7b8916f641b0a` | `valuenum` | 104.0 | -16.3 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `chartevents\|c5af55f2996bd22e` | `chartevents` | `c5af55f2996bd22e` | `valuenum` | 98.6 | 184.1 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |

#### `decimal_shift` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `labevents\|ccf8b8b6d7d19ea8` | `labevents` | `ccf8b8b6d7d19ea8` | `valuenum` | 72.0 | 7200.0 | Value is shifted 10×, 100×, or 1000× the original — lands in the per-itemid clinically impossible band (e.g., glucose > 2000 mg/dL). | medium | 1 | ⚠️ | ☐ |
| `labevents\|5067cd90625ec411` | `labevents` | `5067cd90625ec411` | `valuenum` | 73.0 | 7300.0 | Value is shifted 10×, 100×, or 1000× the original — lands in the per-itemid clinically impossible band (e.g., glucose > 2000 mg/dL). | medium | 1 | ⚠️ | ☐ |
| `labevents\|3d364e4b94e65743` | `labevents` | `3d364e4b94e65743` | `valuenum` | 1.1 | 110.00000000000001 | Value is shifted 10×, 100×, or 1000× the original — lands in the per-itemid clinically impossible band (e.g., glucose > 2000 mg/dL). | medium | 1 | ⚠️ | ☐ |

#### `decimal_shift_rx` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `prescriptions\|e248354367dcd1e3` | `prescriptions` | `e248354367dcd1e3` | `dose_val_rx` | 1 | 100.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|082e818e0af0428a` | `prescriptions` | `082e818e0af0428a` | `dose_val_rx` | 1000 | 100000.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|e6d530a91962cf39` | `prescriptions` | `e6d530a91962cf39` | `dose_val_rx` | 1000 | 100000.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|a4ed17e452b62458` | `prescriptions` | `a4ed17e452b62458` | `dose_val_rx` | 500 | 50000.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|237d7304903cd9df` | `prescriptions` | `237d7304903cd9df` | `dose_val_rx` | 1 | 100.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|707578d9925b3b6e` | `prescriptions` | `707578d9925b3b6e` | `dose_val_rx` | 10 | 1000.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|ecd18b3b536c782b` | `prescriptions` | `ecd18b3b536c782b` | `dose_val_rx` | 100 | 10000.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|1e55f01428b74c8d` | `prescriptions` | `1e55f01428b74c8d` | `dose_val_rx` | 5 | 500.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |

#### `unit_confusion` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `labevents\|e03a0d0250fa9bb2` | `labevents` | `e03a0d0250fa9bb2` | `valuenum` | 3.2 | 282.9 | Value reflects a unit-conversion factor (e.g., creatinine multiplied by 88.42 µmol/L conversion), but the `valueuom` column still reads the original unit — value and unit are inconsistent. | medium | 1 | ⚠️ | ☐ |

#### `valueuom_mismatch` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `labevents\|26010e7a580de438` | `labevents` | `26010e7a580de438` | `valueuom` | umol/L | ng/mL | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `labevents\|a93b42f82651a538` | `labevents` | `a93b42f82651a538` | `valueuom` | mg/24hr | g/dL | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `chartevents\|ab013f28232e3881` | `chartevents` | `ab013f28232e3881` | `valueuom` | dynes.sec.cm-5/m2 | mmol/L | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `chartevents\|b5ba5d5645801ae1` | `chartevents` | `b5ba5d5645801ae1` | `valueuom` | L/min/m2 | ng/mL | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `chartevents\|092ceb9e6eb54622` | `chartevents` | `092ceb9e6eb54622` | `valueuom` | g/dL | mmol/L | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |

### inconsistency


#### `in_table_conflict` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DUP\|labevents\|eafdb880747602f5\|ddc148bc2eb4e804` | `labevents` | `ddc148bc2eb4e804` | `valuenum` | 226.0 | 254.09 | Another row in `labevents` (row_id `eafdb880747602f5`) for the same patient/time/test has `valuenum=226.0` vs. corrupted `254.09` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|e541dffa06acd6fe\|c08d65d9a44eac5c` | `labevents` | `c08d65d9a44eac5c` | `valuenum` | 36.0 | 39.92 | Another row in `labevents` (row_id `e541dffa06acd6fe`) for the same patient/time/test has `valuenum=36.0` vs. corrupted `39.92` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|e758fc6d56c101b0\|bccaea706a26ee4a` | `labevents` | `bccaea706a26ee4a` | `valuenum` | 35.0 | 49.24 | Another row in `labevents` (row_id `e758fc6d56c101b0`) for the same patient/time/test has `valuenum=35.0` vs. corrupted `49.24` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|6b6fe72c20b43cd4\|c8bad5838b152d2b` | `labevents` | `c8bad5838b152d2b` | `valuenum` | 37.0 | 46.91 | Another row in `labevents` (row_id `6b6fe72c20b43cd4`) for the same patient/time/test has `valuenum=37.0` vs. corrupted `46.91` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|5bb317e08764a7ab\|222fbf83983423be` | `labevents` | `222fbf83983423be` | `valuenum` | 0.06 | 0.07 | Another row in `labevents` (row_id `5bb317e08764a7ab`) for the same patient/time/test has `valuenum=0.06` vs. corrupted `0.07` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|9904818aa608de3d\|86e0a1e9b44f4292` | `labevents` | `86e0a1e9b44f4292` | `valuenum` | 104.0 | 135.13 | Another row in `labevents` (row_id `9904818aa608de3d`) for the same patient/time/test has `valuenum=104.0` vs. corrupted `135.13` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|f39fad7fcfad2bfd\|c1815e941b52d88a` | `labevents` | `c1815e941b52d88a` | `valuenum` | 103.0 | 146.03 | Another row in `labevents` (row_id `f39fad7fcfad2bfd`) for the same patient/time/test has `valuenum=103.0` vs. corrupted `146.03` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|9425fcf7a3779a68\|9bcc1f88c2616991` | `labevents` | `9bcc1f88c2616991` | `valuenum` | 6.0 | 7.62 | Another row in `labevents` (row_id `9425fcf7a3779a68`) for the same patient/time/test has `valuenum=6.0` vs. corrupted `7.62` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|23a9f6bc79d0fac9\|9dcb8ec8f1149ffb` | `labevents` | `9dcb8ec8f1149ffb` | `valuenum` | 67.0 | 97.93 | Another row in `labevents` (row_id `23a9f6bc79d0fac9`) for the same patient/time/test has `valuenum=67.0` vs. corrupted `97.93` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|691f6e9268584016\|6b969ed1535d72a7` | `labevents` | `6b969ed1535d72a7` | `valuenum` | 6.0 | 8.43 | Another row in `labevents` (row_id `691f6e9268584016`) for the same patient/time/test has `valuenum=6.0` vs. corrupted `8.43` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|f5b7435bcc99d39b\|4c5e1aa85af75764` | `labevents` | `4c5e1aa85af75764` | `valuenum` | 4.0 | 4.42 | Another row in `labevents` (row_id `f5b7435bcc99d39b`) for the same patient/time/test has `valuenum=4.0` vs. corrupted `4.42` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|8a8117ee66362673\|71916ec15328deb2` | `labevents` | `71916ec15328deb2` | `valuenum` | 2.0 | 2.31 | Another row in `labevents` (row_id `8a8117ee66362673`) for the same patient/time/test has `valuenum=2.0` vs. corrupted `2.31` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|5eec725c09c74750\|3846d56fb84d3732` | `chartevents` | `3846d56fb84d3732` | `valuenum` | 24.0 | 34.47 | Another row in `chartevents` (row_id `5eec725c09c74750`) for the same patient/time/test has `valuenum=24.0` vs. corrupted `34.47` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|a98ecd27a5eb039f\|a29b1bfb8ca0f57c` | `chartevents` | `a29b1bfb8ca0f57c` | `valuenum` | 0.24 | 0.33 | Another row in `chartevents` (row_id `a98ecd27a5eb039f`) for the same patient/time/test has `valuenum=0.24` vs. corrupted `0.33` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|be6fae21b07410f0\|e08a376b772a9c8e` | `chartevents` | `e08a376b772a9c8e` | `valuenum` | 19.3 | 26.37 | Another row in `chartevents` (row_id `be6fae21b07410f0`) for the same patient/time/test has `valuenum=19.3` vs. corrupted `26.37` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|f96e941372485c4d\|d9f666dcc88fd314` | `chartevents` | `d9f666dcc88fd314` | `valuenum` | 2.0 | 2.36 | Another row in `chartevents` (row_id `f96e941372485c4d`) for the same patient/time/test has `valuenum=2.0` vs. corrupted `2.36` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|e4bc766f6e4e5328\|5a9e9e5eb49bb146` | `chartevents` | `5a9e9e5eb49bb146` | `valuenum` | 1.0 | 1.1 | Another row in `chartevents` (row_id `e4bc766f6e4e5328`) for the same patient/time/test has `valuenum=1.0` vs. corrupted `1.1` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|312f646bd70ceb8d\|8bbe7c2f9ff5913e` | `chartevents` | `8bbe7c2f9ff5913e` | `valuenum` | 3.0 | 4.28 | Another row in `chartevents` (row_id `312f646bd70ceb8d`) for the same patient/time/test has `valuenum=3.0` vs. corrupted `4.28` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |

### demographic_conflict


#### `gender_via_ref_range_swap` — 🔴 false-positive risk

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DEMO\|ref_range_swap\|934a18885359a7a3` | `labevents` | `934a18885359a7a3` | `ref_range_lower` | 13.7 | 12.0 | 49 other lab row(s) for this patient (e.g. Hemoglobin (51222), Hematocrit (51221), Creatinine (50912)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; 1 marker prescription(s): Tamsulosin (BPH (enlarged prostate) treatment, male-only); `patients.gender = M` for this patient. | subtle | 53 | 🚩 | ☐ |
| `DEMO\|ref_range_swap\|99f9d3aed2626899` | `labevents` | `99f9d3aed2626899` | `ref_range_lower` | 13.7 | 12.0 | 112 other lab row(s) for this patient (e.g. Creatinine (50912), Hemoglobin (51222), Hematocrit (51221)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; `patients.gender = M` for this patient. | subtle | 115 | 🚩 | ☐ |
| `DEMO\|ref_range_swap\|cf086072a38ce0db` | `labevents` | `cf086072a38ce0db` | `ref_range_lower` | 13.7 | 12.0 | 22 other lab row(s) for this patient (e.g. Hematocrit (51221), Creatinine (50912), Hemoglobin (51222)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; `patients.gender = M` for this patient. | subtle | 25 | 🚩 | ☐ |
| `DEMO\|ref_range_swap\|116f7aa580b1606a` | `labevents` | `116f7aa580b1606a` | `ref_range_lower` | 13.7 | 12.0 | 47 other lab row(s) for this patient (e.g. Hematocrit (51221), Hemoglobin (51222), Creatinine (50912)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; `patients.gender = M` for this patient. | subtle | 50 | 🚩 | ☐ |

### inconsistency


#### `cross_table_conflict` — 🔴 false-positive risk

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DUPX\|labevents\|0d7ba10d006b9c6b\|chartevents\|604f4c6742fad5ee` | `chartevents` | `604f4c6742fad5ee` | `valuenum` | 0.7 | 1.0 | A row in `labevents` (row_id `0d7ba10d006b9c6b`) at the same timestamp for the same patient records `valuenum=0.7` vs. corrupted `1.0` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|1cd1687c4599e6be\|chartevents\|dc03a1ee996975cf` | `chartevents` | `dc03a1ee996975cf` | `valuenum` | 3.3 | 5.4 | A row in `labevents` (row_id `1cd1687c4599e6be`) at the same timestamp for the same patient records `valuenum=3.3` vs. corrupted `5.4` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|faca9f6f02c2b682\|chartevents\|e6dcdfdc7eb95624` | `chartevents` | `e6dcdfdc7eb95624` | `valuenum` | 7.8 | 12.7 | A row in `labevents` (row_id `faca9f6f02c2b682`) at the same timestamp for the same patient records `valuenum=7.8` vs. corrupted `12.7` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|3f6131ac08908835\|chartevents\|3213705bc2da3134` | `chartevents` | `3213705bc2da3134` | `valuenum` | 11.4 | 15.4 | A row in `labevents` (row_id `3f6131ac08908835`) at the same timestamp for the same patient records `valuenum=11.4` vs. corrupted `15.4` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|5799b02bfc1447e0\|chartevents\|5f8048ef58f47337` | `chartevents` | `5f8048ef58f47337` | `valuenum` | 131.0 | 187.0 | A row in `labevents` (row_id `5799b02bfc1447e0`) at the same timestamp for the same patient records `valuenum=131.0` vs. corrupted `187.0` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|3f81857bc801695c\|chartevents\|abb6ca53c32f9141` | `chartevents` | `abb6ca53c32f9141` | `valuenum` | 94.0 | 139.0 | A row in `labevents` (row_id `3f81857bc801695c`) at the same timestamp for the same patient records `valuenum=94.0` vs. corrupted `139.0` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |

---
## task_demographic_conflict

**12 clusters** (_810 labeled rows total, including evidence_)


### demographic_conflict


#### `age_via_patients_change` — 🟢 unambiguous

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DEMO\|age_change\|ed8f5279257d4026` | `patients` | `ed8f5279257d4026` | `anchor_age` | 87.0 | 5.0 | 1 prescription(s) Donepezil (Alzheimer's medication, geriatric-only) — clinically impossible for the corrupted age of 5.0. | medium | 2 |  | ☐ |

#### `gender_via_patients_flip` — 🟢 unambiguous

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DEMO\|patients_flip\|56aa28e6d3d4ea2a` | `patients` | `56aa28e6d3d4ea2a` | `gender` | F | M | 47 of this patient's lab rows (e.g. Creatinine (50912), Hematocrit (51221), Hemoglobin (51222)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`F`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = M` is inconsistent with those reference ranges. | medium | 48 |  | ☐ |
| `DEMO\|patients_flip\|21562e328e2fafa6` | `patients` | `21562e328e2fafa6` | `gender` | M | F | 94 of this patient's lab rows (e.g. Hemoglobin (51222), Hematocrit (51221), Creatinine (50912)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`M`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = F` is inconsistent with those reference ranges. | medium | 95 |  | ☐ |
| `DEMO\|patients_flip\|05fe18dfdaa92be8` | `patients` | `05fe18dfdaa92be8` | `gender` | F | M | 14 of this patient's lab rows (e.g. Creatinine (50912), Hemoglobin (51222), Hematocrit (51221)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`F`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = M` is inconsistent with those reference ranges. | medium | 15 |  | ☐ |
| `DEMO\|patients_flip\|9280f008ce8fc0aa` | `patients` | `9280f008ce8fc0aa` | `gender` | M | F | 177 of this patient's lab rows (e.g. Hemoglobin (51222), Hematocrit (51221), Creatinine (50912)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`M`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = F` is inconsistent with those reference ranges; 7 marker prescription(s): Finasteride (BPH / male-pattern baldness, male-only), Tamsulosin (BPH (enlarged prostate) treatment, male-only). | medium | 185 |  | ☐ |
| `DEMO\|patients_flip\|8411d7ae72ea9dff` | `patients` | `8411d7ae72ea9dff` | `gender` | F | M | 14 of this patient's lab rows (e.g. Creatinine (50912), Hematocrit (51221), Hemoglobin (51222)) carry `ref_range_lower`/`ref_range_upper` set to the canonical band for the patient's *original* gender (`F`) — e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. The flipped `patients.gender = M` is inconsistent with those reference ranges. | medium | 15 |  | ☐ |

#### `gender_via_prescription_swap` — 🟢 unambiguous

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DEMO\|rx_swap\|e56696d6862901c6` | `prescriptions` | `e56696d6862901c6` | `drug` | Acetaminophen IV | Levonorgestrel | Swapped-in drug Levonorgestrel (oral contraceptive, female-only) contradicts `patients.gender = M`; 41 of this patient's lab rows (e.g. Creatinine (50912), Hematocrit (51221), Hemoglobin (51222)) carry sex-specific `ref_range` bands consistent with the patient's true gender, contradicting the swapped-in marker drug; `patients.gender = M` for this patient. | medium | 43 |  | ☐ |

#### `gender_via_ref_range_swap` — 🔴 false-positive risk

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DEMO\|ref_range_swap\|599e52042682ed8b` | `labevents` | `599e52042682ed8b` | `ref_range_lower` | 13.7 | 12.0 | 22 other lab row(s) for this patient (e.g. Hematocrit (51221), Hemoglobin (51222), Creatinine (50912)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; `patients.gender = M` for this patient. | subtle | 25 | 🚩 | ☐ |
| `DEMO\|ref_range_swap\|9c737fe1de61e62d` | `labevents` | `9c737fe1de61e62d` | `ref_range_lower` | 13.7 | 12.0 | 44 other lab row(s) for this patient (e.g. Creatinine (50912), Hematocrit (51221), Hemoglobin (51222)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; 1 marker prescription(s): Tamsulosin (BPH (enlarged prostate) treatment, male-only); `patients.gender = M` for this patient. | subtle | 48 | 🚩 | ☐ |
| `DEMO\|ref_range_swap\|7ed96693aa640158` | `labevents` | `7ed96693aa640158` | `ref_range_lower` | 13.7 | 12.0 | 112 other lab row(s) for this patient (e.g. Creatinine (50912), Hemoglobin (51222), Hematocrit (51221)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; `patients.gender = M` for this patient. | subtle | 115 | 🚩 | ☐ |
| `DEMO\|ref_range_swap\|eb3328c6e25a3466` | `labevents` | `eb3328c6e25a3466` | `ref_range_lower` | 13.7 | 12.0 | 30 other lab row(s) for this patient (e.g. Creatinine (50912), Hemoglobin (51222), Hematocrit (51221)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; `patients.gender = M` for this patient. | subtle | 33 | 🚩 | ☐ |
| `DEMO\|ref_range_swap\|95e236dcca059a65` | `labevents` | `95e236dcca059a65` | `ref_range_lower` | 13.7 | 12.0 | 183 other lab row(s) for this patient (e.g. Hemoglobin (51222), Hematocrit (51221), Creatinine (50912)) still carry the canonical reference-range band matching their true gender; only this single row's `ref_range_lower`/`upper` was overwritten to the opposite-sex band; `patients.gender = M` for this patient. | subtle | 186 | 🚩 | ☐ |

---
## task_impossible_value

**30 clusters** (_30 labeled rows total, including evidence_)


### impossible_value


#### `range_extreme` — 🟢 unambiguous

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `labevents\|9507870f9fb7e066` | `labevents` | `9507870f9fb7e066` | `valuenum` | 1.2 | 675.3 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `labevents\|86d2ccd64597703c` | `labevents` | `86d2ccd64597703c` | `valuenum` | 3.9 | 70.5 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `labevents\|fa50bf1a4271adde` | `labevents` | `fa50bf1a4271adde` | `valuenum` | 134.0 | 629.8 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `chartevents\|796719a1c65a90b5` | `chartevents` | `796719a1c65a90b5` | `valuenum` | 91.0 | 964.3 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `chartevents\|e3fff1a27aa4a018` | `chartevents` | `e3fff1a27aa4a018` | `valuenum` | 54.0 | -113.5 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `chartevents\|af506debfc5c4937` | `chartevents` | `af506debfc5c4937` | `valuenum` | 97.5 | 137.4 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |
| `chartevents\|3f52eea47ebecb0f` | `chartevents` | `3f52eea47ebecb0f` | `valuenum` | 97.0 | 174.0 | Value is outside the physiologically plausible band for this lab/vital (e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, negative blood pressure). | obvious | 1 |  | ☐ |

#### `decimal_shift` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `labevents\|b762f54d97422e22` | `labevents` | `b762f54d97422e22` | `valuenum` | 0.7 | 700.0 | Value is shifted 10×, 100×, or 1000× the original — lands in the per-itemid clinically impossible band (e.g., glucose > 2000 mg/dL). | medium | 1 | ⚠️ | ☐ |
| `labevents\|5b28090792920bfb` | `labevents` | `5b28090792920bfb` | `valuenum` | 1.2 | 120.0 | Value is shifted 10×, 100×, or 1000× the original — lands in the per-itemid clinically impossible band (e.g., glucose > 2000 mg/dL). | medium | 1 | ⚠️ | ☐ |
| `labevents\|d04d950c9d4b0321` | `labevents` | `d04d950c9d4b0321` | `valuenum` | 70.0 | 7000.0 | Value is shifted 10×, 100×, or 1000× the original — lands in the per-itemid clinically impossible band (e.g., glucose > 2000 mg/dL). | medium | 1 | ⚠️ | ☐ |

#### `decimal_shift_rx` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `prescriptions\|5325208f65432267` | `prescriptions` | `5325208f65432267` | `dose_val_rx` | 40 | 4000.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|2ed92ad50b5b4928` | `prescriptions` | `2ed92ad50b5b4928` | `dose_val_rx` | 100 | 10000.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|eb185dbf8a062fd7` | `prescriptions` | `eb185dbf8a062fd7` | `dose_val_rx` | 5 | 500.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|d41fdedebbed9df1` | `prescriptions` | `d41fdedebbed9df1` | `dose_val_rx` | 1 | 100.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|cae9bdd657ccd867` | `prescriptions` | `cae9bdd657ccd867` | `dose_val_rx` | 50 | 5000.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|2efc03bbe48edcec` | `prescriptions` | `2efc03bbe48edcec` | `dose_val_rx` | 145 | 14500.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|947e8c7ff5220b0a` | `prescriptions` | `947e8c7ff5220b0a` | `dose_val_rx` | 1 | 100.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|587d3eef19701461` | `prescriptions` | `587d3eef19701461` | `dose_val_rx` | 1 | 100.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|17acc238edc87236` | `prescriptions` | `17acc238edc87236` | `dose_val_rx` | 1 | 100.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|078eb9dd1b3a3816` | `prescriptions` | `078eb9dd1b3a3816` | `dose_val_rx` | 1 | 100.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|d7b0bf95a8d3f745` | `prescriptions` | `d7b0bf95a8d3f745` | `dose_val_rx` | 21 | 2100.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |
| `prescriptions\|5a563f3d506abec6` | `prescriptions` | `5a563f3d506abec6` | `dose_val_rx` | 2.25 | 225.0 | Prescribed dose is 100× the original — well outside any reasonable dosing range for this drug. | medium | 1 | ⚠️ | ☐ |

#### `unit_confusion` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `labevents\|4a7c6350f43bf30b` | `labevents` | `4a7c6350f43bf30b` | `valuenum` | 70.0 | 4.0 | Value reflects a unit-conversion factor (e.g., creatinine multiplied by 88.42 µmol/L conversion), but the `valueuom` column still reads the original unit — value and unit are inconsistent. | medium | 1 | ⚠️ | ☐ |
| `labevents\|058a4d10277cb2b0` | `labevents` | `058a4d10277cb2b0` | `valuenum` | 7.8 | 689.7 | Value reflects a unit-conversion factor (e.g., creatinine multiplied by 88.42 µmol/L conversion), but the `valueuom` column still reads the original unit — value and unit are inconsistent. | medium | 1 | ⚠️ | ☐ |

#### `valueuom_mismatch` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `labevents\|3b82d696d5dc7ad2` | `labevents` | `3b82d696d5dc7ad2` | `valueuom` | pg | mmol/L | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `labevents\|d80aabfa246a05f2` | `labevents` | `d80aabfa246a05f2` | `valueuom` | pg/mL | mg/L | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `chartevents\|b5d27dad17b5455b` | `chartevents` | `b5d27dad17b5455b` | `valueuom` | g/dl | mg/L | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `chartevents\|02a1d3f54702aef1` | `chartevents` | `02a1d3f54702aef1` | `valueuom` | mL | mg/L | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `chartevents\|f8a9e69fdbcc07bd` | `chartevents` | `f8a9e69fdbcc07bd` | `valueuom` | °C | mg/L | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |
| `chartevents\|3f4f7db27658cd9a` | `chartevents` | `3f4f7db27658cd9a` | `valueuom` | mEq/L | ng/mL | The `valueuom` column has been replaced with a unit that does not correspond to the measured value (e.g., a percentage value labeled as ng/mL). | medium | 1 | ⚠️ | ☐ |

---
## task_inconsistency

**32 clusters** (_64 labeled rows total, including evidence_)


### inconsistency


#### `in_table_conflict` — 🟡 defensible but debatable

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DUP\|labevents\|8fe6160449665bb4\|466efc0ee943d0df` | `labevents` | `466efc0ee943d0df` | `valuenum` | 150.0 | 222.8 | Another row in `labevents` (row_id `8fe6160449665bb4`) for the same patient/time/test has `valuenum=150.0` vs. corrupted `222.8` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|9b0c94aa09501ead\|c637140ce19e889d` | `labevents` | `c637140ce19e889d` | `valuenum` | 0.15 | 0.21 | Another row in `labevents` (row_id `9b0c94aa09501ead`) for the same patient/time/test has `valuenum=0.15` vs. corrupted `0.21` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|7b619a9e12fd047d\|703935cf6938a271` | `labevents` | `703935cf6938a271` | `valuenum` | 21.0 | 25.37 | Another row in `labevents` (row_id `7b619a9e12fd047d`) for the same patient/time/test has `valuenum=21.0` vs. corrupted `25.37` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|491bb18cf8043749\|9f83f2e7465271fb` | `labevents` | `9f83f2e7465271fb` | `valuenum` | 593.0 | 670.34 | Another row in `labevents` (row_id `491bb18cf8043749`) for the same patient/time/test has `valuenum=593.0` vs. corrupted `670.34` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|6ef63b81d22d1c34\|340fc92a4d10bdc6` | `labevents` | `340fc92a4d10bdc6` | `valuenum` | 17.0 | 18.99 | Another row in `labevents` (row_id `6ef63b81d22d1c34`) for the same patient/time/test has `valuenum=17.0` vs. corrupted `18.99` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|e1114e975c99d80a\|68af0f402beccc44` | `labevents` | `68af0f402beccc44` | `valuenum` | 1.0 | 1.29 | Another row in `labevents` (row_id `e1114e975c99d80a`) for the same patient/time/test has `valuenum=1.0` vs. corrupted `1.29` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|ec7510bbe161b26c\|1008e9a55aa0c45b` | `labevents` | `1008e9a55aa0c45b` | `valuenum` | 0.21 | 0.25 | Another row in `labevents` (row_id `ec7510bbe161b26c`) for the same patient/time/test has `valuenum=0.21` vs. corrupted `0.25` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|0f357b01709ab2e7\|ac778c5aa62d4127` | `labevents` | `ac778c5aa62d4127` | `valuenum` | 83.0 | 97.62 | Another row in `labevents` (row_id `0f357b01709ab2e7`) for the same patient/time/test has `valuenum=83.0` vs. corrupted `97.62` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|583e5f719d91b24a\|e9774bfff63cd3c3` | `labevents` | `e9774bfff63cd3c3` | `valuenum` | 1.2 | 1.4 | Another row in `labevents` (row_id `583e5f719d91b24a`) for the same patient/time/test has `valuenum=1.2` vs. corrupted `1.4` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|6943dfe308b34cad\|9cb37bbb7b78870b` | `labevents` | `9cb37bbb7b78870b` | `valuenum` | 219.0 | 265.7 | Another row in `labevents` (row_id `6943dfe308b34cad`) for the same patient/time/test has `valuenum=219.0` vs. corrupted `265.7` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|e0a6e853f5077273\|30492956f2bedc19` | `labevents` | `30492956f2bedc19` | `valuenum` | 0.17 | 0.21 | Another row in `labevents` (row_id `e0a6e853f5077273`) for the same patient/time/test has `valuenum=0.17` vs. corrupted `0.21` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|8374ced1f0f4b96b\|184b7402fddf423d` | `labevents` | `184b7402fddf423d` | `valuenum` | 43.0 | 51.86 | Another row in `labevents` (row_id `8374ced1f0f4b96b`) for the same patient/time/test has `valuenum=43.0` vs. corrupted `51.86` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|8f734e9dc69d9529\|c8e713997799869f` | `labevents` | `c8e713997799869f` | `valuenum` | 125.0 | 185.32 | Another row in `labevents` (row_id `8f734e9dc69d9529`) for the same patient/time/test has `valuenum=125.0` vs. corrupted `185.32` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|feb2104c12fae2fb\|a8c6af85417032cb` | `labevents` | `a8c6af85417032cb` | `valuenum` | 2.0 | 2.32 | Another row in `labevents` (row_id `feb2104c12fae2fb`) for the same patient/time/test has `valuenum=2.0` vs. corrupted `2.32` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|8148d1eb1c2bd87c\|7c2f9a266614aff0` | `labevents` | `7c2f9a266614aff0` | `valuenum` | 158.0 | 236.3 | Another row in `labevents` (row_id `8148d1eb1c2bd87c`) for the same patient/time/test has `valuenum=158.0` vs. corrupted `236.3` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|labevents\|34a807bb9342ba45\|895d8c0b74f53dc6` | `labevents` | `895d8c0b74f53dc6` | `valuenum` | 5.3 | 6.35 | Another row in `labevents` (row_id `34a807bb9342ba45`) for the same patient/time/test has `valuenum=5.3` vs. corrupted `6.35` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|03cb1b041b18f520\|e7cc2aa5f842061b` | `chartevents` | `e7cc2aa5f842061b` | `valuenum` | 360.0 | 409.79 | Another row in `chartevents` (row_id `03cb1b041b18f520`) for the same patient/time/test has `valuenum=360.0` vs. corrupted `409.79` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|3fe971bcf6cfaebb\|faec4aa21d6c651e` | `chartevents` | `faec4aa21d6c651e` | `valuenum` | 35.0 | 43.0 | Another row in `chartevents` (row_id `3fe971bcf6cfaebb`) for the same patient/time/test has `valuenum=35.0` vs. corrupted `43.0` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|67622ea8f6711180\|9e486771169e9845` | `chartevents` | `9e486771169e9845` | `valuenum` | 1.0 | 1.38 | Another row in `chartevents` (row_id `67622ea8f6711180`) for the same patient/time/test has `valuenum=1.0` vs. corrupted `1.38` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|56b848688cc6ba63\|df8ba2d792d9d5c0` | `chartevents` | `df8ba2d792d9d5c0` | `valuenum` | 1.0 | 1.14 | Another row in `chartevents` (row_id `56b848688cc6ba63`) for the same patient/time/test has `valuenum=1.0` vs. corrupted `1.14` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|43ebac411a8bc717\|4be3ad0158751449` | `chartevents` | `4be3ad0158751449` | `valuenum` | 25.0 | 34.23 | Another row in `chartevents` (row_id `43ebac411a8bc717`) for the same patient/time/test has `valuenum=25.0` vs. corrupted `34.23` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|9f5b33a1eb28ba4b\|503ce63cb6b48769` | `chartevents` | `503ce63cb6b48769` | `valuenum` | 107.0 | 157.0 | Another row in `chartevents` (row_id `9f5b33a1eb28ba4b`) for the same patient/time/test has `valuenum=107.0` vs. corrupted `157.0` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|4ba28b538e171534\|37c0fad72abbc77a` | `chartevents` | `37c0fad72abbc77a` | `valuenum` | 1.0 | 1.13 | Another row in `chartevents` (row_id `4ba28b538e171534`) for the same patient/time/test has `valuenum=1.0` vs. corrupted `1.13` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |
| `DUP\|chartevents\|a473ef81d34f49fd\|0d35db8cd1effcae` | `chartevents` | `0d35db8cd1effcae` | `valuenum` | 30.0 | 34.72 | Another row in `chartevents` (row_id `a473ef81d34f49fd`) for the same patient/time/test has `valuenum=30.0` vs. corrupted `34.72` — same conceptual measurement, disagreeing values. | subtle | 2 | ⚠️ | ☐ |

#### `cross_table_conflict` — 🔴 false-positive risk

| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |
|---|---|---|---|---|---|---|---|---|---|---|
| `DUPX\|labevents\|5e4f8a73197a2c6f\|chartevents\|954f52214ada5220` | `chartevents` | `954f52214ada5220` | `valuenum` | 133.0 | 181.0 | A row in `labevents` (row_id `5e4f8a73197a2c6f`) at the same timestamp for the same patient records `valuenum=133.0` vs. corrupted `181.0` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|5450de115d739ca4\|chartevents\|5fc6cdba35af0e2f` | `chartevents` | `5fc6cdba35af0e2f` | `valuenum` | 121.0 | 181.0 | A row in `labevents` (row_id `5450de115d739ca4`) at the same timestamp for the same patient records `valuenum=121.0` vs. corrupted `181.0` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|d99948baeb509078\|chartevents\|7703d96bcfc799d4` | `chartevents` | `7703d96bcfc799d4` | `valuenum` | 9.5 | 15.6 | A row in `labevents` (row_id `d99948baeb509078`) at the same timestamp for the same patient records `valuenum=9.5` vs. corrupted `15.6` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|28832dae7aa2c7d7\|chartevents\|d15ca70742a002c3` | `chartevents` | `d15ca70742a002c3` | `valuenum` | 8.1 | 12.0 | A row in `labevents` (row_id `28832dae7aa2c7d7`) at the same timestamp for the same patient records `valuenum=8.1` vs. corrupted `12.0` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|5cd7532ba52bfdef\|chartevents\|2f92f11bda1208cc` | `chartevents` | `2f92f11bda1208cc` | `valuenum` | 154.0 | 223.0 | A row in `labevents` (row_id `5cd7532ba52bfdef`) at the same timestamp for the same patient records `valuenum=154.0` vs. corrupted `223.0` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|1859e5ca594411f2\|chartevents\|6f92cfbedc21310a` | `chartevents` | `6f92cfbedc21310a` | `valuenum` | 384.0 | 606.0 | A row in `labevents` (row_id `1859e5ca594411f2`) at the same timestamp for the same patient records `valuenum=384.0` vs. corrupted `606.0` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|c98d67aaf857dc61\|chartevents\|55315bef97a5d420` | `chartevents` | `55315bef97a5d420` | `valuenum` | 0.8 | 1.2 | A row in `labevents` (row_id `c98d67aaf857dc61`) at the same timestamp for the same patient records `valuenum=0.8` vs. corrupted `1.2` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
| `DUPX\|labevents\|8b84316d345f9c34\|chartevents\|5926505dcf1f1e4c` | `chartevents` | `5926505dcf1f1e4c` | `valuenum` | 2.2 | 3.5 | A row in `labevents` (row_id `8b84316d345f9c34`) at the same timestamp for the same patient records `valuenum=2.2` vs. corrupted `3.5` — cross-table disagreement on the same measurement. | subtle | 2 | 🚩 | ☐ |
