# Mercury-2 on MedAgentBench (Medical Sphere Evaluation)

- **Source:** https://x.com/MedicalSphereAI/status/2028941856223224173
- **Author:** Medical Sphere (@MedicalSphereAI)
- **Model evaluated:** Mercury-2 (Inception AI)
- **Source read date:** March 17, 2026

## Summary

Medical Sphere ran Mercury-2, a diffusion language model from Inception AI, on MedAgentBench (300 autonomous tasks over a live FHIR EHR). Mercury-2 "holds its own against frontier models," with interesting patterns in where it excels and where it differs from other evaluated models.

This is notable as one of the first independent third-party evaluations of a non-autoregressive (diffusion-based) language model on agentic healthcare benchmarks.

## Key Points

- Mercury-2 is a **diffusion language model** — architecturally distinct from the autoregressive models originally benchmarked in the MedAgentBench paper.
- Performance is described as competitive with frontier models, though specific numbers are only available in the accompanying image (results table).
- The evaluation highlights "genuinely interesting patterns" in Mercury-2's strengths and weaknesses relative to other models, suggesting the diffusion architecture may have a different capability profile on agentic clinical tasks.
- This was the first of two healthcare benchmarks Medical Sphere evaluated Mercury-2 on; the second was not detailed in this tweet.

## Relevance to MedCLI

- **Direct benchmark overlap:** This evaluation uses MedAgentBench, the current benchmark integrated in this repository. Results are directly comparable to our own runs.
- **Architecture diversity:** Diffusion language models represent a fundamentally different generation paradigm. Understanding how they perform on agentic EHR tasks may inform agent design choices (e.g., whether parallel token generation affects multi-step reasoning or tool-call reliability).
- **Third-party validation:** Independent evaluations of MedAgentBench by groups like Medical Sphere help calibrate our own results against a broader set of models and evaluation setups.

## Open Questions

- What are Mercury-2's specific per-category scores on MedAgentBench (query vs. action tasks)?
- How does the diffusion generation process interact with structured tool-call formatting — does it produce more or fewer syntax errors than autoregressive models?
- What was the second healthcare benchmark, and how did Mercury-2 perform on it?
