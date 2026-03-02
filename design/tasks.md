# Agentic EHR Tasks

Brainstorm agentic tasks and survey the literature to identify relevant benchmarks and datasets.

## Candidate Tasks

- **Dataset/schema understanding** — Explore and document the structure of an EHR database (using MIMIC as the reference), including folder layout, file formats, table schemas, and relationships.
- **Factual question answering** — Answer questions grounded in the data, e.g., "How many patients with type-2 diabetes received metformin within 30 days of diagnosis?"
- **Cross-schema ETL & harmonization** — Map a source EHR schema to a target common data model (OMOP CDM, FHIR, [MEDS](https://github.com/Medical-Event-Data-Standard/meds)) by inspecting tables, proposing mappings, writing transformation code, and validating output counts/distributions.
- **Cohort construction & phenotyping** — Given a natural-language description of inclusion/exclusion criteria, write and execute queries to assemble the matching cohort. Operationalize clinical concepts (e.g., "sepsis onset") from raw codes, labs, and notes, and validate against phenotype libraries (PheKB, OHDSI).
- **Clinical outcome prediction with evidence retrieval** — For a target outcome (readmission, mortality, adverse drug event), retrieve relevant features, identify similar historical patients, and produce a risk estimate with cited evidence rows.
- **Patient trajectory summarization** — Generate a longitudinal clinical summary for a given patient — key diagnoses, hospitalizations, medication changes, lab trends — suitable for a clinician or downstream model.
- **Temporal query reasoning** — Answer complex temporal questions requiring multi-hop joins and time-window logic, e.g., "Which patients had a rising creatinine trend in the 48 hours before ICU transfer?"
- **Treatment pathway analysis** — Extract and visualize the most common treatment sequences (first-line → second-line → …) for a given condition, identifying deviations from guideline-recommended pathways.
- **Clinical trial eligibility screening** — Given trial eligibility criteria and a patient ID, retrieve the patient's record and assess each criterion, producing a structured eligibility report with evidence pointers.
- **Medication reconciliation & interaction checking** — Compile a patient's active medication list from scattered prescription/administration records and flag potential drug–drug interactions or contraindications using external tools (e.g., RxNorm, DrugBank API).
- **Data quality auditing** — Detect inconsistencies, missing values, and implausible entries (e.g., negative ages, duplicate encounters, out-of-range lab values) and produce a structured quality report with suggested fixes.
- **Report & letter generation** — Given a patient ID and a purpose (referral letter, discharge summary, insurance pre-authorization), pull structured and unstructured data and draft a document conforming to standard clinical formats.
