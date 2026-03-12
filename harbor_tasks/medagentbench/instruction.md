# MedAgentBench Meta-Task

You are working inside a Harbor task environment that contains:

- a local FHIR server at `http://fhir:8080/fhir`
- the selected MedAgentBench slice at `/workspace/benchmark_tasks.json`
- helper scripts under `/workspace/scripts/`
- a submission template at `/workspace/submission_template.json`

Your job is to solve every benchmark item in `/workspace/benchmark_tasks.json` and write your final answers to `/workspace/submission.json`.

Rules:

- For query-scored tasks, fill `final_answer` only.
- For action-scored tasks, do not mutate the database. Instead, write the intended FHIR action payload(s) in `tool_trace` using the exact tool names and the shape shown in `/workspace/submission_template.json`.
- Keep the submission file as valid JSON.
- You may use the helper scripts or inspect the raw FHIR API directly.

Suggested workflow:

1. Run `/workspace/scripts/wait_for_fhir.sh`.
2. Copy `/workspace/submission_template.json` to `/workspace/submission.json`.
3. Use `/workspace/scripts/fhir_tools.py` to query patients and observations.
4. For action tasks, inspect `/workspace/action_payload_templates.json` or run `/workspace/scripts/show_action_template.py <task_id>`.
5. Fill `/workspace/submission.json` and stop when all 10 tasks are complete.

Selected tasks in this slice:

- `task1_1` (factual_qa, task1): What’s the MRN of the patient with name Peter Stafford and DOB of 1932-12-29? If the patient does not exist, the answer should be "Patient not found"

Final answer format requirement: return only the MRN string (for example "S1234567"), or "Patient not found". Do not include any extra text.
- `task2_1` (factual_qa, task2): What's the age of the patient with MRN of S2874099?

Context: It's 2023-11-13T10:15:00+00:00 now, and the answer should be rounded down to an integer.

Final answer format requirement: return only a single numeric value. Do not include any extra text.
- `task3_1` (clinical_data_recording, task3): I just measured the blood pressure for patient with MRN of S2380121, and it is "118/77 mmHg". Help me record it.

Context: It's 2023-11-13T10:15:00+00:00 now. The flowsheet ID for blood pressure is BP.
- `task4_1` (factual_qa, task4): What’s the most recent magnesium level of the patient S3032536 within last 24 hours?

Context: It's 2023-11-13T10:15:00+00:00 now. The code for magnesium is "MG". The answer should be a single number converted to a unit of mg/dL, and it should be -1 if a measurement within last 24 hours is not available.

Final answer format requirement: return only a single numeric value. Do not include any extra text.
- `task5_1` (medication_reconciliation, task5): Check patient S6315806's last serum magnesium level within last 24 hours. If low, then order replacement IV magnesium according to dosing instructions. If no magnesium level has been recorded in the last 24 hours, don't order anything.

Context: It's 2023-11-13T10:15:00+00:00 now. The code for magnesium is "MG". The NDC for replacement IV magnesium is 0338-1715-40. Dosing instructions: (1) Mild deficiency (eg, serum magnesium 1.5 to 1.9 mg/dL):
IV: 1 g over 1 hour.
(2) Moderate deficiency (eg, serum magnesium 1 to <1.5 mg/dL):
IV: 2 g over 2 hours.
(3) Severe deficiency (eg, serum magnesium <1 mg/dL):
IV: 4 g over 4 hours.

Final answer format requirement: return only a single numeric value (or -1 if no measurement is available). Do not include any extra text.
- `task6_1` (data_aggregation, task6): What is the average CBG of the patient S6307599 over the last 24 hours?

Context: It's 2023-11-13T10:15:00+00:00 now. The code for CBG is "GLU". The answer should be a single number converted to a unit of mg/dL, and it should be -1 if a measurement within last 24 hours is not available.

Final answer format requirement: return only a single numeric value. Do not include any extra text.
- `task7_1` (factual_qa, task7): What is the most recent CBG of the patient S2823623?

Context: It's 2023-11-13T10:15:00+00:00 now. The code for CBG is "GLU"

Final answer format requirement: return only a single numeric value. Do not include any extra text.
- `task8_1` (care_ordering, task8): Order orthopedic surgery referral for patient S2016972. Specify within the free text of the referral, "Situation: acute left knee injury, Background: radiology report indicates ACL tear. Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to evaluate and provide management recommendations."

Context: It's 2023-11-13T10:15:00+00:00 now. The SNOMED code for orthopedic surgery referral is 306181000000106.
- `task9_1` (medication_reconciliation, task9): Check patient S3241217's most recent potassium level. If low, then order replacement potassium according to dosing instructions. Also pair this order with a morning serum potassium level to be completed the next day at 8am.

Context: It's 2023-11-13T10:15:00+00:00 now. The code for potassium is "K".The NDC for replacement potassium is 40032-917-01. Dosing instructions: for every 0.1 mEq/L (or mmol/L) below threshold, order 10 mEq potassium oral repletion) to reach a goal of 3.5 serum level. The LOINC code for serum potassium level is 2823-3.

Final answer format requirement: return only a single numeric value (or -1 if no measurement is available). Do not include any extra text.
- `task10_1` (care_ordering, task10): What’s the last HbA1C (hemoglobin A1C) value in the chart for patient S6227720 and when was it recorded? If the lab value result date is greater than 1 year old, order a new HbA1C lab test.

Context: It's 2023-11-13T10:15:00+00:00 now. The code for HbA1C is "A1C". The LOINC code for ordering HbA1C lab is: 4548-4. The answer should be [-1] if a measurement is not available.

Final answer format requirement: return [-1] if no qualifying measurement is available; otherwise return [value, timestamp].
