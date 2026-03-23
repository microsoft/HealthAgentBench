# Agentic EHR Tasks

Brainstorm agentic tasks and survey the literature to identify relevant benchmarks and datasets.

## Benchmarks

Track benchmark integrations and benchmark candidates here. Any benchmark considered for this repo should first get an entry in `design/related_work/`, and only then be added to one of the tables below. The `Details` column points to that related-work note.

### Integrated

| Benchmark | Task Directory | Description | Notes | Details |
| --- | --- | --- | --- | --- |
| MedAgentBench | `medagentbench/` | Interactive EHR benchmark focused on multi-step retrieval, reasoning, and structured action tasks over clinical data. | Harbor-generated benchmark task built from raw benchmark assets under `scripts/medagentbench/`. | [MedAgentBench](related_work/medagentbench_2501.14654.md) |

### Planned

| Benchmark | Description | Notes | Details |
| --- | --- | --- | --- |
| EHRSHOT | Longitudinal structured EHR benchmark for few-shot evaluation of foundation models across 15 prediction tasks. | Relevant benchmark candidate for structured-EHR evaluation, but not an interactive agent benchmark; would require a different task shape from MedAgentBench. | [EHRSHOT](related_work/ehrshot_2307.02028.md) |
| MedCalc-Bench | Medical-calculation benchmark with 1,000+ manually reviewed instances across 55 calculator tasks. | Strong benchmark candidate for quantitative clinical reasoning, but static rather than interactive; would likely need a non-Harbor-environment task shape. | [MedCalc-Bench](related_work/medcalc_bench_2406.12036.md) |

### Review Queue

| Benchmark | Description | Notes | Details |
| --- | --- | --- | --- |
| HEARTS | Health time-series reasoning benchmark spanning 16 datasets, 12 domains, and 110 tasks over diverse physiological and behavioral signals. | Relevant if MedCLI expands into health time-series and file/code-based analysis; needs review because it is far from the current structured-EHR and interactive workflow focus. | [HEARTS](related_work/li2026b.md) |
| DeepRare / Rare Disease Diagnosis Agent | Agentic rare-disease diagnosis system using phenotype, free-text, and genomic inputs with traceable evidence-linked reasoning. | Strongly relevant to agentic health workflows, but it is a system paper rather than a clean benchmark package; needs review before deciding whether it should drive a new benchmark family. | [DeepRare](related_work/deeprare_rare_disease_2026.md) |
| Medea | Verification-aware omics AI agent for therapeutic discovery using long-horizon tool-based analyses across datasets, models, and literature. | Strongly relevant to biomedical agent design, but it is a discovery-system paper rather than a benchmark package and sits outside the current repo scope; needs review before any integration decision. | [Medea](related_work/medea_omics_agent_2026.md) |
| Autonomous Oncology Decision-Making Agent | Multimodal oncology agent combining GPT-4 with pathology, radiology, retrieval, and oncology-specific tools for personalized clinical decisions. | Strongly relevant to clinical agent design, but it is a system-validation paper over a small case set rather than a reusable benchmark package; needs review before any scope decision. | [Oncology Agent](related_work/oncology_agent_nature_cancer_2025.md) |

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
