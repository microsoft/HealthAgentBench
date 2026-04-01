# Related Work

This note prioritizes papers from 2025 to now, then backfills older benchmark lineage where a reviewer is likely to cite it against the paper. The search was intentionally high recall: recent arXiv papers, major conference proceedings, major medical journals, and benchmark-adjacent system papers that overlap with the MedCLI thesis.

## Executive Takeaway

I do not currently see a single paper that makes MedCLI unnecessary. I do see a crowded and rapidly moving cluster of partially overlapping work: healthcare agent benchmarks such as [MedAgentBench](https://arxiv.org/abs/2501.14654), [MedAgentBoard](https://arxiv.org/abs/2505.12371), [ClinicalAgent Bench (CAB)](https://arxiv.org/abs/2410.17657), executable environments such as [MedChain](https://arxiv.org/abs/2412.01605), [CP-Env](https://arxiv.org/abs/2512.10206), and framework papers such as [MedMASLab](https://arxiv.org/abs/2603.09909). The novelty risk is therefore not "someone already did exactly this," but rather that reviewers can argue the space is already partially covered unless the paper makes a narrower and more defensible claim.

The safest positioning is not "the first healthcare agent benchmark" or even "the first healthcare benchmark suite" in the absolute sense. The stronger claim is that MedCLI is a unified, executable, Harbor-based suite for healthcare agents that standardizes environment, tools, instructions, tests, and evaluation across heterogeneous benchmark families, with an explicit goal of ongoing maintenance and longitudinal progress tracking.

## Closest Prior Work

### MedAgentBench

[MedAgentBench](https://arxiv.org/abs/2501.14654) is the most direct predecessor to the current repo because it is already integrated into MedCLI. It is clearly relevant and must be cited prominently. Its strength is that it is explicitly agentic and medically grounded. Its limitation, relative to the MedCLI thesis, is that it is one benchmark rather than a broader maintained suite spanning multiple benchmark families and environment shapes.

### MedAgentBoard

[MedAgentBoard](https://arxiv.org/abs/2505.12371) is one of the highest-risk comparator papers. It is a comprehensive benchmark for evaluating multi-agent collaboration, single-LLM systems, and conventional methods across four medical task categories spanning text, images, structured EHR data, and workflow automation. This overlaps strongly with the "suite" and "cross-modality" parts of the MedCLI story. The main difference is that MedAgentBoard is a benchmark study centered on comparing agentic versus non-agentic methods on a curated set of task families, whereas MedCLI is trying to define a reusable execution and evaluation substrate for continuously maintained agentic benchmarks.

### ClinicalAgent Bench (CAB)

[ClinicalAgent Bench (CAB)](https://arxiv.org/abs/2410.17657), introduced through the [ReflecTool](https://aclanthology.org/2025.acl-long.663/) paper, is another high-risk comparator. CAB covers 18 tasks across five clinical dimensions and is explicitly designed to evaluate clinical agents rather than static medical QA alone. This directly undercuts any claim that healthcare has no agent benchmark at all. The difference is that CAB is still a fixed benchmark embedded inside a specific paper-and-method package, whereas MedCLI is aiming at a benchmark suite and common execution framework that can host multiple benchmark families under one interface.

### MedChain

[MedChain](https://arxiv.org/abs/2412.01605) is a strong comparator because it frames clinical decision making as a personalized, interactive, sequential benchmark across five stages of clinical workflow. It pushes toward exactly the sort of realism and interactivity that a reviewer may expect from an "agentic" healthcare benchmark. The difference is that MedChain is a single benchmark centered on sequential clinical decision making, whereas MedCLI is broader in benchmark scope and more explicit about common packaging, environments, and evaluation infrastructure.

### CP-Env

[CP-Env](https://arxiv.org/abs/2512.10206) is particularly important because it is an end-to-end clinical-pathway environment rather than a static benchmark. It simulates a hospital ecosystem with branching pathways, patient and physician agents, tool use, and long-horizon evaluation. This directly overlaps with the environment-centric part of the MedCLI thesis. If MedCLI does not integrate similarly interactive benchmarks, reviewers may reasonably ask why a new framework is needed beyond CP-Env and related environments.

### MedMASLab

[MedMASLab](https://arxiv.org/abs/2603.09909) is a major threat to the "unified evaluation framework" claim. It presents itself as a unified orchestration framework and benchmarking platform for multimodal medical multi-agent systems, integrating multiple architectures, modalities, and datasets under standardized interfaces. If MedCLI wants to claim framework novelty, it must explain how it differs from MedMASLab. The defensible distinction is that MedMASLab is centered on multimodal medical multi-agent systems and their semantic evaluation, whereas MedCLI is trying to serve as a broader benchmark suite interface spanning heterogeneous task environments, including terminal-style and tool-executing tasks, with a simpler benchmark packaging and maintenance story.

## Healthcare Agent Benchmarks

### Agent-native and benchmark-first work

- [MedAgentBench](https://arxiv.org/abs/2501.14654): directly relevant and already in the repo. Strong evidence that healthcare agent benchmarking is active and recent.
- [MedAgentBoard](https://arxiv.org/abs/2505.12371): broad medical benchmark covering medical QA, medical VQA, lay summary generation, structured EHR prediction, and workflow automation. High novelty-risk comparator because it is already a cross-modality medical benchmark study.
- [ClinicalAgent Bench (CAB)](https://arxiv.org/abs/2410.17657): 18 tasks across five realistic clinical dimensions. High-risk evidence against any claim that healthcare lacks agent benchmarks altogether.
- [CP-Env](https://arxiv.org/abs/2512.10206): controllable hospital environment for end-to-end clinical pathways. High-risk comparator for environment-based evaluation.
- [MedChain](https://arxiv.org/abs/2412.01605): interactive sequential benchmark over five stages of clinical workflow. Strong comparator for sequential, personalized clinical decision-making evaluation.
- [3MDBench](https://arxiv.org/abs/2504.13861) and its [EMNLP 2025 version](https://aclanthology.org/2025.emnlp-main.1353/): a medical multimodal multi-agent dialogue benchmark for telemedicine. Important because it operationalizes interactive doctor-patient dialogue rather than single-turn QA.
- [Doctorina MedBench](https://arxiv.org/abs/2603.25821): a very recent end-to-end evaluation framework for agent-based medical AI built around realistic physician-patient interactions, diagnostic reasoning, and treatment recommendations. This is a direct comparator for dialogue-centric clinical-agent evaluation.
- [LifeAgentBench](https://arxiv.org/abs/2601.13880): a benchmark for long-horizon, cross-dimensional digital-health reasoning for personal health assistants. Relevant because it expands healthcare-agent benchmarking beyond hospital and EHR settings.
- [HealthBench](https://arxiv.org/abs/2505.08775) and the [OpenAI release note](https://openai.com/index/healthbench/): not an executable agent benchmark in the same sense as MedCLI, but a broad, high-visibility health evaluation benchmark covering thousands of realistic conversations. This will likely be familiar to reviewers.
- [MedBench v4](https://arxiv.org/abs/2511.14439): a large-scale Chinese benchmark infrastructure with explicit tracks for LLMs, multimodal models, and intelligent agents. It is not identical to MedCLI, but it is strong evidence that broad benchmark-platform work in medical AI is already underway.
- [A benchmark for evaluating diagnostic questioning efficiency of LLMs in patient conversations](https://www.nature.com/articles/s41598-026-37022-y): narrower than MedCLI, but directly relevant because it evaluates interactive questioning strategy rather than static answer accuracy.

### What this cluster implies

This literature clearly weakens any blanket statement that healthcare lacks agent benchmarks. A more accurate statement is that healthcare still lacks a widely adopted, benchmark-suite-level interface that standardizes heterogeneous agent benchmarks under one common execution and evaluation substrate. That is a narrower claim, but it is much more defensible.

## Healthcare Agent Systems and Evaluations

Several papers are not benchmark papers in the strict sense, but a reviewer could still cite them as evidence that the field already evaluates healthcare agents in realistic settings.

- [AgentEHR](https://arxiv.org/abs/2601.13918): an autonomous clinical decision-making system built around longitudinal EHR workflows. Important because it looks like the sort of system MedCLI would want to evaluate.
- [DeepRare](https://www.nature.com/articles/s41586-025-10097-9): a rare-disease diagnosis agent with tool use and traceable reasoning. Not a benchmark paper, but highly relevant evidence that serious healthcare-agent evaluation is already happening in domain-specific settings.
- [Autonomous oncology decision-making agent](https://www.nature.com/articles/s43018-025-00991-6): a system paper rather than a reusable benchmark, but directly relevant to agent evaluation in medically consequential settings.
- [BioMedAgent](https://www.nature.com/articles/s41551-026-01634-6): biomedical rather than clinical, but relevant because it pairs an agent system with its own biomedical benchmark family.
- [Biomni](https://pmc.ncbi.nlm.nih.gov/articles/PMC12157518/): a general-purpose biomedical AI agent evaluated on new task collections and realistic scientific workflows. This is more biomedical-research-oriented than healthcare-delivery-oriented, but it is an important adjacent comparison for the broader "health and biomedicine" framing.
- [MEDDxAgent](https://aclanthology.org/2025.acl-long.677/): relevant as a diagnosis-agent paper that demonstrates realistic task-oriented evaluation even if it is not itself a benchmark suite.
- [MATRIX](https://arxiv.org/abs/2508.19163): a structured framework for safety-oriented evaluation of clinical dialogue agents with simulated patients and hazard-based scenario design. It is narrower than MedCLI, but relevant because it turns safety evaluation into a scalable clinical-agent testing workflow.

The reviewer risk from these papers is not that they invalidate MedCLI directly, but that they weaken broad claims about novelty if the paper ignores them. They should be used to motivate why a common benchmark suite is valuable precisely because evaluation is currently being reinvented separately across disease-specific and workflow-specific systems.

## Adjacent Healthcare Benchmarks

These papers matter because they cover important healthcare capabilities even when they are not agent-native benchmark suites.

- [EHRSHOT](https://arxiv.org/abs/2307.02028): structured longitudinal EHR few-shot benchmark. Important for the structured-EHR axis of MedCLI.
- [MedCalc-Bench](https://arxiv.org/abs/2406.12036): focused benchmark for medical calculations. Important for quantitative clinical reasoning.
- [HEARTS](https://arxiv.org/abs/2603.06638): unified benchmark for health time-series reasoning across many modalities and domains. Important if MedCLI wants to argue coverage beyond text and EHR workflows.
- [EHRSQL](https://arxiv.org/abs/2301.07695): text-to-SQL over EHR data. Not agent-native, but directly relevant to EHR tool use and retrieval.
- [EHRXQA](https://arxiv.org/abs/2310.18652): EHR question answering with realistic data grounding. Useful benchmark lineage for EHR reasoning.
- [DrugEHRQA](https://aclanthology.org/2022.lrec-1.535/): focused clinical QA dataset over EHR-style data, useful as benchmark lineage.
- [CCBench](https://pmc.ncbi.nlm.nih.gov/articles/PMC12102327/): a domain-specific medical benchmark for cervical cytology screening; narrower, but useful as evidence that the field is rich in specialized healthcare evaluation sets.
- [MedRepBench](https://blog.yueqianlin.com/daily-publication/250826/): benchmark for medical report understanding and structured extraction. Lower priority, but potentially useful if the suite expands toward reporting tasks.
- [PatientSim](https://arxiv.org/abs/2505.17818): a persona-driven simulator for realistic doctor-patient interactions. More infrastructure than benchmark, but highly relevant to interactive clinical evaluation.

These papers support one of the central arguments in the draft: the landscape is fragmented. Healthcare evaluation is distributed across many narrow datasets, simulators, and task-specific benchmarks, with different interfaces and assumptions.

## General-Domain Agent Benchmark Context

The paper also needs a short general-domain benchmark backdrop so reviewers can see that the MedCLI framing is aligned with current agent evaluation practice rather than invented ad hoc for healthcare.

- [SkillsBench](https://arxiv.org/abs/2602.12670): a strong example of a general-domain benchmark that decomposes and evaluates agent skills systematically. This is particularly relevant to the MedCLI motivation around explicit abstractions and capability coverage.
- [OSWorld](https://arxiv.org/abs/2404.07972): important because it popularized real computer environments and open-ended multimodal tasks. It is a useful precedent for environment-first evaluation.
- [GAIA](https://arxiv.org/abs/2311.12983): important as a broad assistant benchmark for multi-step reasoning and tool use.
- [WebArena](https://arxiv.org/abs/2307.13854): useful precedent for realistic, reproducible environments.
- [TheAgentCompany](https://arxiv.org/abs/2412.14161): relevant for the idea that broad agent progress should be measured in realistic, consequential task environments.

These papers are not competitors in the healthcare sense, but they are important for supporting the MedCLI claim that explicit environments, tools, instructions, and reproducible execution are now standard expectations for agent benchmarks.

## What Still Appears Distinct About MedCLI

Given the literature above, the distinctiveness of MedCLI should be framed in a restrained way.

### 1. A benchmark suite interface, not just another single benchmark

Many relevant papers contribute one benchmark, one environment, or one agent-and-benchmark package. MedCLI is better positioned as the common interface that hosts multiple heterogeneous healthcare benchmarks under one execution and evaluation framework.

### 2. Executable, agent-native packaging across heterogeneous benchmark families

The clearest distinction is not just breadth of topics, but common executable packaging. MedCLI should emphasize that benchmarks are exposed through standardized environments, tools, instructions, tests, and result artifacts, rather than through a collection of bespoke scripts and one-off evaluation codebases.

### 3. Reproducibility and maintenance as first-class goals

Several papers release code and datasets, but relatively few center long-term maintenance, standardized execution, and repeatable cross-agent evaluation as the core research contribution. This is where the Harbor-first design and benchmark packaging story matter most.

### 4. Cross-benchmark comparability inside one framework

Papers such as MedAgentBoard and MedMASLab already move toward broader medical evaluation, so this claim has to be careful. The strongest version is that MedCLI tries to make benchmark families comparable even when they differ in environment shape, modality, and task interface.

## Reviewer Attack Surfaces

### Attack 1: "Healthcare already has agent benchmarks."

This objection is valid if the draft says healthcare lacks agent benchmarks entirely. CAB, MedAgentBench, MedAgentBoard, MedChain, CP-Env, and 3MDBench are enough to refute that wording. The paper should instead say there is no widely adopted, unified, and maintained benchmark-suite interface for healthcare agents.

### Attack 2: "This is just a repackaging of existing benchmarks."

This is the strongest likely attack. The answer has to be concrete: MedCLI is valuable only if it provides standard executable interfaces, evaluation outputs, agent portability, and easier cross-benchmark comparison that the original benchmark releases do not already provide. If the implementation does not substantively reduce integration friction, the paper will read as packaging rather than contribution.

### Attack 3: "MedMASLab or MedAgentBoard already provide the unified evaluation story."

This is the main threat to the framework claim. The response should be that those papers are important and must be discussed explicitly, but that they target narrower slices of the space: medical multi-agent comparison in MedAgentBoard, and multimodal medical MAS orchestration in MedMASLab. MedCLI needs to show that it is broader in benchmark-family coverage and simpler as a reusable benchmark substrate.

### Attack 4: "HealthBench already covers broad healthcare evaluation."

HealthBench is a serious comparator for broad healthcare evaluation, but it is not the same kind of artifact. It is closer to a large conversational benchmark than to an executable multi-environment agent benchmark suite. The paper should say this directly rather than sidestepping HealthBench.

### Attack 5: "The suite is too small to justify the word suite."

This is not a literature issue alone; it is a paper-scoping issue. The first submission should include enough genuinely distinct benchmark families to make the suite framing credible. If the paper launches with too few integrated benchmarks, reviewers will compare it unfavorably with broader papers such as MedAgentBoard, MedMASLab, or HEARTS.

## Priority Citation Table

| Paper | Year | Venue / Status | Category | Why It Matters | Novelty Risk | Positioning | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [MedAgentBench](https://arxiv.org/abs/2501.14654) | 2025 | arXiv | Closest prior work | Directly agentic, medically grounded benchmark already integrated into this repo | High | Cite as one benchmark family inside MedCLI, not as the whole story | Must discuss explicitly |
| [MedAgentBoard](https://arxiv.org/abs/2505.12371) | 2025 | arXiv | Closest prior work | Broad medical benchmark across text, vision, EHR, and workflow automation | High | Distinguish MedCLI as benchmark-suite infrastructure rather than one benchmark study | Must discuss explicitly |
| [ClinicalAgent Bench / ReflecTool](https://arxiv.org/abs/2410.17657) | 2024 / 2025 | arXiv; ACL 2025 | Closest prior work | Explicit medical agent benchmark with 18 tasks across five dimensions | High | Use it to soften any claim that healthcare lacks agent benchmarks entirely | Must discuss explicitly |
| [MedChain](https://arxiv.org/abs/2412.01605) | 2024 | arXiv | Closest prior work | Interactive, sequential, workflow-oriented clinical benchmark | High | Distinguish MedCLI as a suite interface rather than another workflow benchmark | Must discuss explicitly |
| [CP-Env](https://arxiv.org/abs/2512.10206) | 2025 | arXiv | Closest prior work | Controllable hospital environment with long-horizon pathway evaluation | High | Important comparator for environment-centric evaluation | Must discuss explicitly |
| [MedMASLab](https://arxiv.org/abs/2603.09909) | 2026 | arXiv | Closest prior work | Unified orchestration and benchmarking platform for multimodal medical multi-agent systems | High | Biggest challenge to the unified-framework claim; differentiate carefully | Must discuss explicitly |
| [HealthBench](https://arxiv.org/abs/2505.08775) | 2025 | arXiv; OpenAI release | Healthcare benchmark | Broad, visible health benchmark with realistic conversations and physician-authored rubrics | Medium | Distinguish conversational health evaluation from executable multi-environment agent benchmarking | Must cite |
| [3MDBench](https://arxiv.org/abs/2504.13861) | 2025 | arXiv; EMNLP 2025 | Healthcare benchmark | Multimodal dialogue benchmark for medical consultations | Medium | Important evidence that interactive medical-agent evaluation is already advancing | Must cite |
| [Doctorina MedBench](https://arxiv.org/abs/2603.25821) | 2026 | arXiv | Healthcare benchmark | End-to-end evaluation of agent-based medical AI through realistic physician-patient dialogue | Medium | Directly relevant to dialogue-centric clinical-agent evaluation; cite so reviewers do not think it was missed | Must cite |
| [LifeAgentBench](https://arxiv.org/abs/2601.13880) | 2026 | arXiv | Healthcare benchmark | Long-horizon digital-health assistant benchmark | Medium | Helps broaden the healthcare scope beyond hospital/EHR settings | Must cite |
| [MedBench v4](https://arxiv.org/abs/2511.14439) | 2025 | arXiv | Healthcare benchmark | Large-scale medical benchmark infrastructure with dedicated agent track | Medium | Evidence that benchmark-platform work in medicine is already moving toward agent evaluation | Must cite |
| [AgentEHR](https://arxiv.org/abs/2601.13918) | 2026 | arXiv | Healthcare agent system | Strong system paper around autonomous EHR decision-making | Medium | Use as evidence that evaluation is being reinvented per system; motivates need for common suite | Must cite |
| [DeepRare](https://www.nature.com/articles/s41586-025-10097-9) | 2026 | Nature | Healthcare agent system | High-profile rare disease agent with tool use and traceable reasoning | Medium | Cite as domain-specific agent evaluation, not benchmark-suite competition | Must cite |
| [Autonomous oncology decision-making agent](https://www.nature.com/articles/s43018-025-00991-6) | 2025 | Nature Cancer | Healthcare agent system | Strong disease-specific agent evaluation in oncology | Medium | Cite as domain-specific system evidence | Must cite |
| [BioMedAgent](https://www.nature.com/articles/s41551-026-01634-6) | 2026 | Nature Biomedical Engineering | Biomedical agent system | Biomedical agent paired with benchmark tasks | Medium | Relevant especially if MedCLI broadens toward biomedical tasks | Must cite |
| [Biomni](https://pmc.ncbi.nlm.nih.gov/articles/PMC12157518/) | 2025 | bioRxiv / PMC mirror | Biomedical agent system | Strong adjacent biomedical-agent benchmark and workflow paper | Medium | Important adjacent context, especially for tool-using biomedical agents | Cite and discuss limits |
| [MATRIX](https://arxiv.org/abs/2508.19163) | 2025 | arXiv | Healthcare agent system | Safety-oriented conversational evaluation framework with simulated patients and hazard detection | Medium | Important if MedCLI makes safety or dialogue-evaluation claims | Must cite |
| [HEARTS](https://arxiv.org/abs/2603.06638) | 2026 | arXiv | Adjacent healthcare benchmark | Broad health time-series reasoning benchmark | Medium | Useful if MedCLI includes time-series tasks; supports multi-modality claim | Must cite |
| [EHRSHOT](https://arxiv.org/abs/2307.02028) | 2023 | arXiv | Adjacent healthcare benchmark | Longitudinal structured-EHR benchmark | Low | Benchmark lineage for EHR tasks, not direct competition | Must cite |
| [MedCalc-Bench](https://arxiv.org/abs/2406.12036) | 2024 | arXiv | Adjacent healthcare benchmark | Focused benchmark for medical calculation reasoning | Low | Supports clinical reasoning coverage argument | Must cite |
| [EHRSQL](https://arxiv.org/abs/2301.07695) | 2023 | arXiv | Adjacent healthcare benchmark | Important lineage for EHR querying and structured reasoning | Low | Cite if EHR interaction is a benchmark family in the suite | Cite if relevant |
| [EHRXQA](https://arxiv.org/abs/2310.18652) | 2023 | arXiv | Adjacent healthcare benchmark | Important EHR QA lineage | Low | Useful benchmark ancestry for EHR tasks | Cite if relevant |
| [SkillsBench](https://arxiv.org/abs/2602.12670) | 2026 | arXiv | General-domain benchmark context | Good precedent for capability-oriented agent benchmarking | Low | Use to frame the agent-benchmark design language, not healthcare novelty | Must cite |
| [OSWorld](https://arxiv.org/abs/2404.07972) | 2024 | arXiv | General-domain benchmark context | Strong precedent for real executable environments | Low | Supports the environment-first benchmark framing | Must cite |
| [GAIA](https://arxiv.org/abs/2311.12983) | 2023 | arXiv | General-domain benchmark context | Widely recognized benchmark for general assistants | Low | Context for multi-step assistant evaluation | Must cite |
| [WebArena](https://arxiv.org/abs/2307.13854) | 2023 | arXiv | General-domain benchmark context | Strong precedent for realistic, reproducible agent environments | Low | Supports environment and reproducibility framing | Cite if space allows |
| [TheAgentCompany](https://arxiv.org/abs/2412.14161) | 2024 | arXiv | General-domain benchmark context | Shows how realistic agent benchmarking is framed outside healthcare | Low | Helps justify suite-level evaluation design | Cite if space allows |

## Bottom Line for the Paper

The literature supports the overall problem statement, but only if the claims are sharpened. The paper should not argue that healthcare has no agent benchmarks. It should argue that healthcare still lacks a broadly adopted, unified, executable, and maintainable benchmark-suite interface for agent evaluation across heterogeneous health tasks. That is the space where MedCLI still appears justified.
