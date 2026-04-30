# Tumor Area Selection in Digital Pathology

- Upstream data:
  - [GDC / TCGA slide images](https://gdc.cancer.gov/access-data/gdc-data-portal)
  - [CAMELYON16 dataset](https://camelyon16.grand-challenge.org/) and the public AWS mirror `s3://camelyon-dataset/CAMELYON16/`
  - [Prov-GigaPath](https://github.com/prov-gigapath/prov-gigapath)
- Access:
  - TCGA whole-slide images are downloadable from the public GDC API by file UUID.
  - CAMELYON16 whole-slide TIFFs, masks, and XML annotations are publicly mirrored on AWS.
  - Prov-GigaPath inference requires accepting the Hugging Face model terms and providing `HF_TOKEN`.
- Source read date: April 28, 2026.
- Upstream citations:
  - Tomczak et al., *The Cancer Genome Atlas (TCGA): an immeasurable source of knowledge* (Contemporary Oncology, 2015).
  - Litjens et al., *1399 H&E-stained sentinel lymph node sections of breast cancer patients: the CAMELYON dataset* (GigaScience, 2018).
  - Xu et al., *A whole-slide foundation model for digital pathology from real-world data* (Nature, 2024).

## Summary

Tumor detection and localization in digital pathology is a natural agentic benchmark because the input is a gigapixel whole-slide image rather than a short fixed-context example. A capable system must decide where to look, how to move from coarse overview to fine inspection and pick the tumor rich regions. This makes the task qualitatively different from static image classification or patch-level prediction: the challenge is not only recognizing tumor, but also navigating a large visual search space efficiently and reliably.

We use two public resources for this setting. TCGA provides broad access to real-world H&E slides across many cancer types and includes sample-type metadata that can support slide-level tumor-versus-normal evaluation. CAMELYON16 provides whole-slide lymph-node metastasis images with pixel-level tumor annotations, making it appropriate for tile-level or region-level localization evaluation. 

## Main Contributions

1. Frames tumor area selection from pathology slides as a tool-using, multi-step agent benchmark rather than only a static classifier benchmark.
2. Combines a broad public cancer-slide resource (TCGA) with a gold-annotated localization resource (CAMELYON16) to cover both detection and localization.
3. Introduces a benchmark shape where weak heuristics and pathology foundation-model signals are available as tools, but none are perfectly aligned with the final answer.
4. Emphasizes structured outputs and verifier-friendly evaluation instead of open-ended pathology narration.

## Method and Setup (High Level)

- Input modality: whole-slide H&E pathology images.
- Agent interaction model: slide navigation and inspection through predefined viewing tools.
- Coarse-to-fine workflow:
  - inspect a thumbnail or slide overview
  - identify tissue-bearing or suspicious regions
  - zoom to local tiles or neighborhoods
  - combine visual evidence with auxiliary signals
  - return a structured tumor prediction
- TCGA supports slide-level tumor presence classification.
- CAMELYON16 supports tile- or region-level tumor localization using mask-derived gold labels.
- Candidate tools can include:
  - thumbnail extraction
  - tile and region retrieval
  - tissue masking
  - neighborhood exploration
  - weak tile-scoring heuristics
  - pathology foundation-model attention or saliency maps

## Key Findings from Upstream Resources

- CAMELYON16 remains one of the clearest public sources for tumor-localization evaluation because it includes lesion annotations rather than only slide labels.
- Whole-slide pathology changes the benchmark design space substantially: exhaustive inspection is expensive, and useful intermediate tools are often noisy rather than decisive.
- Foundation models such as Prov-GigaPath make it realistic to expose strong but imperfect pathology priors without turning the task into supervised training.

## Limitations and Integration Questions

- TCGA is not a pathology benchmark release in the narrow sense; it is a large public cancer-data resource that needs benchmark curation and label-hiding care.
- CAMELYON16 is strong for localization, but the dataset is relatively small and focused on a specific metastasis-detection setting rather than broad pathology coverage.
- Whole-slide tasks are expensive in storage, I/O, and visual search space, so benchmark design has to account for runtime stability and tractable evaluation.
- Foundation-model signals can be useful, but a benchmark should avoid reducing the task to a single pretrained heatmap lookup.
- Tile- or region-level gold construction requires explicit choices about magnification, tile size, tumor-area thresholds, and handling of non-tissue regions.

## Relevance to MedCLI

This task family is highly relevant to MedCLI's broader interest in tool-using medical agents emulating real-world clinical and research workflows.

### Alignment

- Strong emphasis on multimodal clinical reasoning rather than text-only QA.
- Naturally requires sequential tool use over large structured assets.
- Supports structured, verifier-friendly outputs for both detection and localization.
- Creates a realistic setting where agent success depends on search strategy as well as local visual judgment.

### Differences

- Operates over gigapixel pathology images rather than EHR tables, FHIR records, or free-text notes.
- The core difficulty is visual navigation and localization, not database querying or prose generation.
- Public-image handling and caching matter much more than in the current tabular or text-heavy benchmarks.

## Implications for This Repository

1. Pathology should be treated as a distinct multimodal benchmark family rather than a small extension of existing EHR-oriented tasks.
2. The most natural packaging unit is a per-slide task with hidden labels and a tool-mediated slide interface.
3. Public-data bootstrap and lazy caching are likely to be core infrastructure patterns for future whole-slide-image tasks.
4. This benchmark can serve as a reusable template for other pathology workflows that require region search, localization, or morphology-guided decisions.
