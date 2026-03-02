# Tool Suite Design

Design and implement a suite of tools that frontier models can invoke via function calling to complete agentic tasks.

## Database & Query Tools

- **SQL executor** — Run read-only SQL queries against an EHR database (e.g., PostgreSQL/SQLite for MIMIC) and return results as a table or JSON.
- **Schema inspector** — List tables, columns, data types, foreign keys, and row counts for a given database, so the agent can orient itself before writing queries.
- **Query validator** — Dry-run a SQL query (EXPLAIN) to catch syntax errors and estimate cost before execution.

## Data Analysis & Computation

- **Python sandbox** — Execute arbitrary Python/pandas code in a sandboxed environment for data wrangling, statistical tests, and feature engineering.
- **Statistical calculator** — Compute summary statistics, confidence intervals, p-values, and odds ratios without writing full scripts.
- **Visualization generator** — Produce charts (histograms, Kaplan–Meier curves, Sankey diagrams for treatment pathways) from query results and return image files.

## Medical Knowledge & Coding

- **ICD/CPT/LOINC code lookup** — Search and resolve medical codes by description or code, with cross-walks between coding systems (ICD-9 ↔ ICD-10, LOINC ↔ local lab codes).
- **RxNorm / DrugBank API** — Look up drug information, map between brand/generic names, and check drug–drug interactions and contraindications.
- **Clinical guideline retriever** — Search and retrieve relevant sections from clinical practice guidelines (e.g., NCCN, AHA) given a condition or treatment question.
- **PubMed search** — Query PubMed for relevant literature given a clinical question, returning structured citation results.

## EHR-Specific Utilities

- **FHIR client** — Read and write FHIR resources (Patient, Observation, MedicationRequest, etc.) against a FHIR server endpoint.
- **ClinicalTrials.gov search** — Query the ClinicalTrials.gov API for recruiting trials matching patient characteristics and return structured eligibility criteria.
- **De-identification checker** — Scan text or query results for potential PHI (names, dates, MRNs) and flag or redact before output.

## File & Format Tools

- **Web fetcher** — Retrieve and parse online content in case external knowledge is needed.
- **Bash tools** — Execute shell commands for data processing pipelines.
- **CSV/Parquet reader** — Load and preview tabular files (with optional filtering and sampling) without requiring the agent to write boilerplate I/O code.
- **Document parser** — Extract structured information from clinical notes, PDFs, or CDA documents.
- **Schema mapper** — Given a source and target schema (e.g., raw MIMIC → OMOP CDM), suggest column-level mappings and generate transformation code stubs.
