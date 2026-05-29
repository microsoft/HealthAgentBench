# ehr_data_quality — Clinical bands & thresholds for review

All hardcoded clinical constants used by the error injector. **Review each value against clinical literature / your domain knowledge** and mark anything you want changed.

Source files:
- `scripts/ehr_data_quality/inject.py` — used during error injection.
- `scripts/ehr_data_quality/reference_solver.py` — used by the agent-baseline reference solver.

These two are intentionally kept *slightly* out of sync: the injector's "extreme" band is a subset of the solver's "plausible" band, so the solver can still detect injections it wasn't explicitly told about. Diffs between the two are flagged below.

---

## 1. Per-itemid plausible/extreme bands (lab & chart values)

Used by `range_extreme` (samples from extreme band) and `decimal_shift` (multiplies original to land in extreme band).

**Schema:** `(name, plausible_lo, plausible_hi, extreme_lo, extreme_hi)` from `inject.py:RANGE_VIOLATIONS`.

### `labevents`

| itemid | Lab | Plausible band | Extreme band (injected) | Solver-side plausible | Review |
|---|---|---|---|---|---|
| 50912 | Creatinine (mg/dL) | 0.1 – 20.0 | **80.0 – 999.9** | 0.05 – 25.0 | ☐ |
| 50931 | Glucose (mg/dL) | 30.0 – 800.0 | **2000.0 – 9999.0** | 20.0 – 1000.0 | ☐ |
| 50971 | Potassium (mEq/L) | 1.0 – 9.0 | **25.0 – 99.0** | 0.5 – 10.0 | ☐ |
| 50983 | Sodium (mEq/L) | 100.0 – 200.0 | **400.0 – 999.0** | 90.0 – 220.0 | ☐ |
| 50885 | Bilirubin total (mg/dL) | _(not injected)_ | _(not injected)_ | 0.1 – 30.0 | ☐ |

### `chartevents`

| itemid | Measurement | Plausible band | Extreme band (injected) | Solver-side plausible | Review |
|---|---|---|---|---|---|
| 220045 | Heart rate (bpm) | 20 – 250 | **400.0 – 999.0** | 15 – 260 | ☐ |
| 220179 | SBP non-invasive (mmHg) | 40 – 250 | **−100.0 – −10.0** _(negative BP)_ | 30 – 260 | ☐ |
| 220180 | DBP non-invasive (mmHg) | 20 – 200 | **−150.0 – −50.0** _(negative BP)_ | 15 – 210 | ☐ |
| 223761 | Temp (°F) | 80.0 – 110.0 | **130.0 – 200.0** | 75.0 – 115.0 | ☐ |
| 220277 | SpO2 (%) | 50 – 100 | **130.0 – 200.0** _(>100%)_ | 40 – 105 | ☐ |

**Notes for review:**
- The plausible bands are the eligibility filter for `decimal_shift`; the extreme bands are the target landing zone after the multiplier. The split must be wide enough that ×100 of a plausible value lands in the extreme band.
- **Glucose plausible_hi = 800** is wide enough to cover real DKA/HHS presentations — this was the root cause of the "720 plausible" issue. ×100 of 72 = 7200 ∈ [2000, 9999] ✓.
- **Sodium plausible_hi = 200** may be too wide (severe hypernatremia is usually 160–180). Consider tightening to 180 if you want a more conservative eligibility filter.
- **HR plausible_hi = 250** — typical max ICU HR is ~220 (SVT); 250 is at the edge of physiologic.
- **Temp plausible_hi = 110°F** — covers heat-stroke (105–110°F). 110 is the absolute physiologic ceiling.

---

## 2. Sex-specific lab reference ranges

Used by `gender_via_ref_range_swap`: overwrites `ref_range_lower`/`ref_range_upper` with the opposite-sex canonical band.

**Source:** `inject.py:SEX_REF_RANGES`.

| itemid | Lab | Male band | Female band | Review |
|---|---|---|---|---|
| 51222 | Hemoglobin (g/dL) | 13.5 – 17.5 | 12.0 – 15.5 | ☐ |
| 51221 | Hematocrit (%) | 41.0 – 50.0 | 36.0 – 45.0 | ☐ |
| 50912 | Creatinine (mg/dL) | 0.7 – 1.3 | 0.5 – 1.0 | ☐ |

**Notes for review:**
- These are textbook adult ranges. Variant institutional/manufacturer bands exist but these are mainstream.
- **Creatinine** sex-split is narrower (delta ~0.2 mg/dL); a swapped row is harder to detect than hemoglobin/hematocrit. May want to drop Creatinine from this list if the M/F gap is too subtle.

---

## 3. Sex-only / sex-skewed lab analytes

Standalone evidence: presence of one of these labs IS the gender signal.

**Source:** `inject.py:SEX_ONLY_LAB_ITEMIDS`.

| itemid | Lab | Gender skew | Review |
|---|---|---|---|
| 50974 | PSA (Prostate-Specific Antigen) | M-only | ☐ |
| 51085 | HCG (Human Chorionic Gonadotropin) | F-overwhelming | ☐ |

**Notes for review:** HCG can be elevated in M (testicular germ-cell tumors), but it's overwhelmingly used in pregnancy testing. Worth confirming.

---

## 4. Unit-confusion conversion factors

Used by `unit_confusion`: applies a real unit-conversion factor as a corruption (value reads correct in the wrong unit, but the `valueuom` column still claims the original unit).

**Source:** `inject.py:UNIT_CONFUSION_FACTORS`.

| itemid | Lab | Original unit | Wrong unit | Conversion factor | Review |
|---|---|---|---|---|---|
| 50912 | Creatinine | mg/dL | µmol/L | ×88.42 | ☐ |
| 50931 | Glucose | mg/dL | mmol/L | ×0.0555 | ☐ |
| 50885 | Bilirubin total | mg/dL | µmol/L | ×17.10 | ☐ |

These are correct textbook unit conversions. Mark for review only if you want to add/remove labs.

**Wrong units pool** (used by `valueuom_mismatch`): `mmol/L`, `ng/mL`, `g/dL`, `%`, `mg/L` (from `inject.py:WRONG_UNITS`).

---

## 5. Lab ↔ chart paired itemids

Used by `cross_table_conflict`: injects a chartevents row at the same timestamp as a labevents row with a disagreeing value.

**Source:** `inject.py:LAB_CHART_PAIRS` and `reference_solver.py:LAB_CHART_PAIRS` (same).

| Analyte | labevents itemid | chartevents itemid | Review |
|---|---|---|---|
| Glucose | 50931 | 225664 | ☐ |
| Sodium | 50983 | 220645 | ☐ |
| Creatinine | 50912 | 220615 | ☐ |
| Hemoglobin | 51222 | 220228 | ☐ |

---

## 6. Per-itemid output precision (decimal places)

Used to round synthetic mutated values so they don't stand out via IEEE-754 float artifacts (e.g., `120.50000000000001`).

**Source:** `inject.py:DEVICE_PRECISION` (default: 2 decimals).

| itemid | Where | Decimals | Review |
|---|---|---|---|
| 225664 | chart: bedside glucose | 0 | ☐ |
| 220645 | chart: serum sodium | 0 | ☐ |
| 220615 | chart: creatinine | 1 | ☐ |
| 220228 | chart: hemoglobin | 1 | ☐ |
| 50912 | lab: creatinine | 1 | ☐ |
| 50931 | lab: glucose | 0 | ☐ |
| 50971 | lab: potassium | 1 | ☐ |
| 50983 | lab: sodium | 0 | ☐ |
| 50885 | lab: bilirubin total | 1 | ☐ |
| 51221 | lab: hematocrit | 1 | ☐ |
| 51222 | lab: hemoglobin | 1 | ☐ |
| 51181 | lab: immature granulocytes | 2 | ☐ |
| 51478 | lab: generic urine analyte | 1 | ☐ |

---

## 7. Inconsistency multiplier ranges

How much two "should-agree" rows are forced to disagree. Sampled uniformly from `rng.uniform(...)`.

| Subtype | Multiplier range | Code location | Review |
|---|---|---|---|
| `in_table_conflict` | **×1.10 – ×1.50** (10–50% disagreement) | `inject.py:833` | ☐ |
| `cross_table_conflict` | **×1.30 – ×1.70** (30–70% disagreement) | `inject.py:943` | ☐ |

**Notes for review:**
- `cross_table_conflict` ×1.30 may be too narrow — labs vs. bedside devices routinely disagree by 20–30% in real EHRs. Consider raising the floor to 1.50 or 2.0 so the injected conflict is unambiguously larger than analytic noise.
- `in_table_conflict` ×1.10 (10% disagreement) is small — duplicate lab rows can legitimately differ by ~10% due to repeat-draw timing. Consider raising floor to 1.20.

---

## 8. Solver-side z-score thresholds

Reference solver flags rows beyond these z-scores. **Not used by injector** — only by the reference baseline.

**Source:** `reference_solver.py`.

| Constant | Value | What it controls | Review |
|---|---|---|---|
| `Z_THRESHOLD` | 8.0 | Per-itemid outlier flag (lab/chart values) | ☐ |
| `DOSE_Z_THRESHOLD` | 10.0 | Per-drug dose outlier flag | ☐ |
| `CROSS_TABLE_DIFF_THRESHOLD` | 0.40 (40%) | Lab-vs-chart relative difference flag | ☐ |

---

## 9. Gender-marker drug lists

**Source:** `inject.py:GENDER_DRUG_HINTS` (full list, used for evidence aggregation) + `inject.py:EXCLUDED_GENDER_MARKER_DRUGS` (subset NOT used as injection corruption target).

### Female-marker drugs

| Drug | Used as injection corruption? | Clinical use | Review |
|---|---|---|---|
| Estradiol | ✗ excluded — M off-label use (prostate Ca, trans HRT) | estrogen replacement | ☐ |
| Estrogen | ✗ excluded — same | estrogen replacement | ☐ |
| Tamoxifen | ✓ used | breast cancer | ☐ |
| Anastrozole | ✓ used | breast cancer aromatase inhibitor | ☐ |
| Levonorgestrel | ✓ used | oral / emergency contraceptive | ☐ |
| Norethindrone | ✓ used | oral contraceptive | ☐ |
| Medroxyprogesterone | ✓ used | contraceptive, but ⚠️ also used in M for prostate Ca | ☐ |

### Male-marker drugs

| Drug | Used as injection corruption? | Clinical use | Review |
|---|---|---|---|
| Sildenafil | ✓ used | ED, but ⚠️ also F use for pulmonary hypertension | ☐ |
| Tadalafil | ✓ used | ED, but ⚠️ also F use for pulmonary hypertension | ☐ |
| Vardenafil | ✓ used | ED | ☐ |
| Finasteride | ✓ used | BPH / male-pattern baldness, but ⚠️ used in F for hirsutism | ☐ |
| Dutasteride | ✓ used | BPH, but ⚠️ used off-label in F for hair loss | ☐ |
| Tamsulosin | ✗ excluded — F off-label use (kidney stones, urinary retention) | BPH | ☐ |
| Testosterone | ✓ used | testosterone replacement, but ⚠️ also F use for low libido | ☐ |

**Notes for review:**
- The ⚠️ flagged drugs (Medroxyprogesterone, Sildenafil, Tadalafil, Finasteride, Dutasteride, Testosterone) have documented cross-sex off-label use. They are *less clean* than Levonorgestrel / Tamoxifen / Anastrozole as gender markers. If you want a stricter gold, consider also excluding them.

---

## 10. Geriatric-marker drugs

Used by `age_via_patients_change`: rewrites `anchor_age` to a child-age value (5) for a patient whose prescriptions clearly indicate a geriatric patient.

**Source:** `inject.py:GERIATRIC_DRUG_HINTS` and `reference_solver.py:GERIATRIC_DRUGS` (same list).

| Drug | Indication | Geriatric-only? | Review |
|---|---|---|---|
| Donepezil | Alzheimer's disease | Yes (very rare pediatric autism off-label use) | ☐ |
| Memantine | Alzheimer's disease | Yes (very rare pediatric autism off-label use) | ☐ |
| Rivastigmine | Alzheimer's / Parkinson's dementia | Yes | ☐ |
| Galantamine | Alzheimer's disease | Yes | ☐ |

These are clean — all four are dementia/Alzheimer's medications with effectively no pediatric use.

---

## How to use this review

For each row you want to change, replace `☐` with `✏️` and add a note. When done, I'll patch the constants in `inject.py` and `reference_solver.py` accordingly.

For the per-itemid bands (Section 1), if you tighten any value, also consider whether the solver-side band in Section 1's last column should follow.
