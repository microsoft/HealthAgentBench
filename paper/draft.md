# Working Title

MedCLI: A Unified Suite of Agentic Benchmarks for Healthcare

> [[NeurIPS 2026 D&B Track](https://neurips.cc/Conferences/2026/Dates)]: Due on May 6. The timeline is tight, but use it as a forcing function for scope, execution, and writing.

## Abstract Sketch

We aim to build a suite of healthcare benchmarks for evaluating AI agents under realistic, medically grounded task settings. Existing healthcare benchmarks are often narrow in scope, inconsistent in setup, difficult to reproduce, or outdated relative to modern agent abstractions such as environments, tools, and explicit instructions. This makes it hard to compare systems fairly or to track progress in agentic AI for healthcare over time.

Our project introduces a suite of agentic healthcare benchmarks that are either newly created or redesigned for agent evaluation. These benchmarks expose clear concepts of environment, tools, instructions, and task interfaces while requiring substantial medical competence across domains such as EHR workflows, medical images, time series, rare disease reasoning, and other health data modalities. We unify these benchmarks under a common evaluation framework and use the resulting suite to evaluate a broad set of LLM agents, characterize current strengths and weaknesses, and identify open challenges for healthcare agents. By releasing and continuously maintaining this benchmark suite, we aim to provide the community with a practical interface for measuring and tracking progress in agentic AI for healthcare.

## Introduction / Motivation

### 1. A lack of healthcare benchmarks for AI agents

There is currently no widely adopted benchmark suite for evaluating agentic AI in healthcare as a coherent field. Existing healthcare benchmarks tend to emphasize a specific domain, narrow task family, or one-off setup. As a result, they do not provide a clear picture of how capable an agent is across the broader space of healthcare-relevant work.

### 2. Existing benchmarks are too narrow to reflect general healthcare-agent capability

Many existing healthcare benchmarks focus on a specialized domain, a narrow task family, or a single evaluation setup. These benchmarks can still be valuable, but they do not capture the broader range of capabilities required for healthcare agents that must operate across different data modalities, reasoning styles, and interaction settings.

### 3. Benchmark setups are fragmented and hard to reproduce

This problem is compounded by the fact that many existing benchmarks have incompatible assumptions, inconsistent code quality, or highly bespoke data and evaluation pipelines. Even when the underlying tasks are valuable, the surrounding setup is often difficult to reproduce, standardize, or compare fairly across agents.

### 4. Many benchmarks are outdated relative to modern agent abstractions

At the same time, AI agents are evolving quickly. Many older healthcare benchmarks were not designed with explicit concepts such as environments, tools, instructions, and action interfaces in mind. Those abstractions are now central to agent evaluation in the general domain, and they are equally important in healthcare.

Taken together, these issues make it hard to track progress in agentic AI for healthcare. The field lacks a shared, agent-native benchmark suite that is broad enough to be meaningful, standardized enough to be reproducible, and medically grounded enough to matter.

## Why Existing Benchmarks Are Not Enough

Current healthcare benchmarks are often limited in one or more of the following ways:

- they focus on a single narrow domain or task type
- they use incompatible or highly bespoke benchmark setups
- they lack clean and reusable concepts of environment, tools, and instructions
- they are not maintained in a way that keeps pace with modern agents
- they make cross-agent comparison and longitudinal tracking difficult

These weaknesses do not mean the benchmarks are unimportant. Many are valuable and should be preserved. But they are not sufficient, by themselves, to serve as a standardized interface for tracking the progress of healthcare agents as a field.

## Our Thesis

Healthcare needs a unified, agent-native benchmark suite that makes progress in medical AI agents measurable, reproducible, comparable, and continuously trackable over time.

## Contributions

We aim to make five main contributions.

### 1. A suite of agentic healthcare benchmarks

We introduce a suite of healthcare benchmarks that are specifically created or redesigned to evaluate agentic AI systems rather than static prediction or question answering alone.

### 2. Agent-native benchmark design with strong medical grounding

Our benchmarks adopt explicit abstractions such as environment, instructions, and tests, which are common in modern general-domain agent benchmarks. At the same time, they require deep medical domain knowledge across diverse modalities and task settings, including medical images, time series, rare diseases, EHR workflows, etc. This combination is what differentiates the suite from general-domain agent benchmarks.

### 3. A unified evaluation framework

We place these benchmarks under a common evaluation framework so that different agents can be run, measured, and compared in a more consistent way. This reduces setup fragmentation and makes reporting much more straightforward.

### 4. A broad empirical study of healthcare agents

We evaluate a comprehensive set of LLM agents on the benchmark suite, analyze their strengths and limitations, and discuss what the results imply about the current state and future direction of agentic AI in healthcare.

### 5. A living benchmark suite for tracking progress in healthcare agents

The goal is not just to release a one-time benchmark package, but to establish a living benchmark suite for healthcare agents. We aim to make the suite available for community use, maintain benchmark quality over time, update benchmark implementations as agent-evaluation standards improve, and add new benchmarks as important healthcare domains emerge. If successful, this suite can become a community-facing interface for tracking progress in agentic AI for healthcare.

## Evaluation Story

The paper should tell a clear empirical story:

- a common framework can make diverse healthcare-agent benchmarks comparable
- current agents show uneven performance across benchmark types
- progress in general-domain agents does not automatically transfer to healthcare
- tool use, environment interaction, and domain grounding remain major bottlenecks

The evaluation section should support both aggregate conclusions and benchmark-specific analysis. It should make clear not only which agents perform best, but also where and why they fail.

## Open Questions / Missing Evidence

Several important questions remain open and should guide the next phase of the project.

- Which benchmarks will be mature enough to include in the first paper submission?
- What minimum benchmark-suite size is sufficient to justify the “suite” framing?
- How broad should the first release be across modalities and task families?
- Which claims in the draft need direct empirical evidence versus broader framing support?
- How should benchmark updates be handled after the initial release so that comparisons remain meaningful over time?

This draft should continue evolving as implementation and evaluation decisions become more concrete.
