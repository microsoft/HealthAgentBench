# Agentic EHR Tasks

Brainstorm agentic tasks and survey the literature to identify relevant benchmarks and datasets.

## Benchmarks

Track benchmark integrations and benchmark candidates here. Any benchmark considered for this repo should first get an entry in `design/related_work/`, and only then be added to one of the tables below. The `Details` column points to that related-work note.

### Integrated

| Benchmark | Task Directory | Description | Notes | Details |
| --- | --- | --- | --- | --- |
| MedAgentBench | `medagentbench/` | Interactive EHR benchmark focused on multi-step retrieval, reasoning, and structured action tasks over clinical data. | Harbor-generated benchmark task built from raw benchmark assets under `scripts/medagentbench/`. | [MedAgentBench](related_work/medagentbench_2501.14654.md) |
| EHRSQL | `ehrsql/` | Text-to-SQL benchmark over EHR databases (MIMIC-III, eICU). Agent generates SQL queries or identifies unanswerable questions. | Tasks generated via `scripts/ehrsql/generate_harbor_tasks.py`. | [EHRSQL](related_work/ehrsql_2301.07695.md) |
| MIMIC-IV MEDS Extraction ETL | `mimic_iv_meds/` | ETL benchmark for converting the open MIMIC-IV demo dataset into MEDS by following the pinned upstream `MIMIC_IV_MEDS` repo. | Adapted Harbor task with staged demo input, agent-run `uv` setup, and directory-output verification against a gold summary. | [MIMIC_IV_MEDS v0.0.7](related_work/mimic_iv_meds_0.0.7.md) |

### Planned

| Benchmark | Description | Notes | Details |
| --- | --- | --- | --- |
| EHRSHOT | Longitudinal structured EHR benchmark for few-shot evaluation of foundation models across 15 prediction tasks. | Relevant benchmark candidate for structured-EHR evaluation, but not an interactive agent benchmark; would require a different task shape from MedAgentBench. | [EHRSHOT](related_work/ehrshot_2307.02028.md) |
| MedCalc-Bench | Medical-calculation benchmark with 1,000+ manually reviewed instances across 55 calculator tasks. | Strong benchmark candidate for quantitative clinical reasoning, but static rather than interactive; would likely need a non-Harbor-environment task shape. | [MedCalc-Bench](related_work/medcalc_bench_2406.12036.md) |
| Medical Billing Code | Medical billing and coding benchmark for generating ICD/CPT codes from clinical documentation. Agent reads clinical notes and assigns appropriate billing codes. | Relevant to real-world clinical NLP workflows; would require coding ontology data and evaluation against standard code sets. | |

### Review Queue

| Benchmark | Description | Notes | Details |
| --- | --- | --- | --- |
| HEARTS | Health time-series reasoning benchmark spanning 16 datasets, 12 domains, and 110 tasks over diverse physiological and behavioral signals. | Relevant if MedCLI expands into health time-series and file/code-based analysis; needs review because it is far from the current structured-EHR and interactive workflow focus. | [HEARTS](related_work/li2026b.md) |
| DeepRare / Rare Disease Diagnosis Agent | Agentic rare-disease diagnosis system using phenotype, free-text, and genomic inputs with traceable evidence-linked reasoning. | Strongly relevant to agentic health workflows, but it is a system paper rather than a clean benchmark package; needs review before deciding whether it should drive a new benchmark family. | [DeepRare](related_work/deeprare_rare_disease_2026.md) |
| Medea | Verification-aware omics AI agent for therapeutic discovery using long-horizon tool-based analyses across datasets, models, and literature. | Strongly relevant to biomedical agent design, but it is a discovery-system paper rather than a benchmark package and sits outside the current repo scope; needs review before any integration decision. | [Medea](related_work/medea_omics_agent_2026.md) |
| Autonomous Oncology Decision-Making Agent | Multimodal oncology agent combining GPT-4 with pathology, radiology, retrieval, and oncology-specific tools for personalized clinical decisions. | Strongly relevant to clinical agent design, but it is a system-validation paper over a small case set rather than a reusable benchmark package; needs review before any scope decision. | [Oncology Agent](related_work/oncology_agent_nature_cancer_2025.md) |

## Candidate Tasks

- **Dataset/schema understanding** — Explore and document the structure of an EHR database (using MIMIC as the reference), including folder layout, file formats, table schemas, and relationships.
    - This could be a tool. Not necessarily we have to evaluate it.
- **Factual question answering** — Answer questions grounded in the data, e.g., "How many patients with type-2 diabetes received metformin within 30 days of diagnosis?"
    - [MedAgentBench](https://arxiv.org/abs/2501.14654), external data, <span style="color:red">already ceiling performance (>90)</span> — [notes](related_work/medagentbench_2501.14654.md)
    - [EHRSQL](https://github.com/glee4810/EHRSQL), MIMIC-III + eICU, MIMIC-IV  — [notes](related_work/ehrsql_2301.07695.md)
    - [EHRXQA](https://github.com/baeseongsu/ehrxqa), MIMIC-IV + MIMIC-CXR — [notes](related_work/ehrxqa_2310.18652.md)
    - [DrugEHRQA](https://aclanthology.org/2022.lrec-1.117.pdf), MIMIC-III — [notes](related_work/drugehrqa_2022.lrec.md)
- **Cross-schema ETL & harmonization** — Map a source EHR schema to a target common data model (OMOP CDM, FHIR, [MEDS](https://github.com/Medical-Event-Data-Standard/meds)) by inspecting tables, proposing mappings, writing transformation code, and validating output counts/distributions.
    - [Medical Billing Code](https://github.com/JoakimEdin/medical-coding-reproducibility), MIMIC-IV — [notes](related_work/medical_coding_reproducibility_2304.10909.md)
    - Many existing repos that offer MIMIC to OMOP, CDM, FHIR transformations. What will we offer that is different? (shall we say that we will improve over the existing baselines?) How about we treat them as tools for solving a more meaningful downstream task (eg. for event modelling?)
        - MIMIC to FHIR: https://physionet.org/content/mimic-iv-fhir/2.1/
        - MIMIC to OMOP: https://github.com/OHDSI/MIMIC
        - MIMIC to MEDS: https://github.com/Medical-Event-Data-Standard/MIMIC_IV_MEDS

- **Cohort construction & phenotyping** — Given a natural-language description of inclusion/exclusion criteria, write and execute queries to assemble the matching cohort. Operationalize clinical concepts (e.g., "sepsis onset") from raw codes, labs, and notes, and validate against phenotype libraries (PheKB, OHDSI).
    - [n2c2](https://huggingface.co/datasets/bigbio/n2c2_2018_track1?utm_source=chatgpt.com), external data, <span style="color:red">ceiling performance (>90)</span> — [notes](related_work/n2c2_2018_track1.md)
- **Clinical outcome prediction with evidence retrieval** — For a target outcome (readmission, mortality, adverse drug event), retrieve relevant features, identify similar historical patients, and produce a risk estimate with cited evidence rows.
    - [Exploring Scaling Laws for EHR Foundation Models](https://arxiv.org/abs/2505.22964): predict survival, length of stay and readmission risks based on longitudinal input — [notes](related_work/ehr_scaling_laws_2505.22964.md)
    - [AgentEHR](https://arxiv.org/abs/2601.13918) Challenge models for diagnosis based on longitudinal history — [notes](related_work/agentehr_2601.13918.md)
- **Patient trajectory summarization** — Generate a longitudinal clinical summary for a given patient — key diagnoses, hospitalizations, medication changes, lab trends — suitable for a clinician or downstream model.
    - [BHC summary](https://pubmed.ncbi.nlm.nih.gov/39786555/), MIMIC-IV, a summarization task for MIMIC longitudinal patient trajectory. But be cautious about the mismatch of automated BLEU etc. metrics with human preference. — [notes](related_work/bhc_summary_39786555.md)
    - Could be a tool for downtream task. Not necessarily for evaluation
- **Temporal query reasoning** — Answer complex temporal questions requiring multi-hop joins and time-window logic, e.g., "Which patients had a rising creatinine trend in the 48 hours before ICU transfer?"
    - Already included in Factual question answering section
- **Treatment pathway analysis** — Extract and visualize the most common treatment sequences (first-line → second-line → …) for a given condition, identifying deviations from guideline-recommended pathways.
    - Providence related data
- **Clinical trial eligibility screening** — Given trial eligibility criteria and a patient ID, retrieve the patient's record and assess each criterion, producing a structured eligibility report with evidence pointers.
- **Medication reconciliation & interaction checking** — Compile a patient's active medication list from scattered prescription/administration records and flag potential drug–drug interactions or contraindications using external tools (e.g., RxNorm, DrugBank API).
    - [SafeDrug](https://github.com/ycq091044/SafeDrug): Given patient history, predict the recommended drugs without drug-drug adverse interactions. — [notes](related_work/safedrug_2105.02711.md)
- **Data quality auditing** — Detect inconsistencies, missing values, and implausible entries (e.g., negative ages, duplicate encounters, out-of-range lab values) and produce a structured quality report with suggested fixes.
    - We can easily test it with synthetic "error" records
    - We can do a quality check with clinicians on what the model proposes. 
- **Report & letter generation** — Given a patient ID and a purpose (referral letter, discharge summary, insurance pre-authorization), pull structured and unstructured data and draft a document conforming to standard clinical formats.
    - We can leverage this as a tool rather than performing intrinsic evaluation
