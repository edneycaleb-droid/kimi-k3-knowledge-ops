---
name: long-context-retention-lab
description: Measure instruction retention, contradiction handling, retrieval precision, and context compression behavior as Kimi context grows.
metadata:
  version: "1.0.0"
  profile: "evaluation"
---

# Long Context Retention Lab

## Contract

**Input:** pinned corpus, model identity, context budgets, needle set, distractors, and acceptance thresholds.

**Output:** retention curves, miss taxonomy, contradiction behavior, latency/cost evidence, and context-routing recommendations.

**Done:** results are reproducible from corpus and fixture digests and distinguish retrieval failure from reasoning failure.

**Non-goals:** advertising a maximum context size, using private data without approval, or treating one synthetic benchmark as general intelligence.

## Workflow

1. Hash the corpus and record the tokenizer, model, runtime, hardware, and prompt template.
2. Create needles covering exact recall, paraphrase, multi-hop linkage, temporal updates, negative instructions, and unresolved contradiction.
3. Insert calibrated distractors and near-duplicate false matches.
4. Run increasing context bands with fixed seeds where supported.
5. Separate failures into not retrieved, retrieved but ignored, instruction collision, hallucinated support, stale claim, and output truncation.
6. Compare full-context loading against tiered retrieval and compressed summaries.
7. Report accuracy, abstention, latency, token use, and cost without hiding failed runs.

## Limits

`max_context_bands: 6`, `max_attempts: 2`. Stop if corpus identity, model version, or raw result retention is unavailable.

## Output

Return `environment`, `corpus_digest`, `retention_curve`, `miss_taxonomy`, `compression_comparison`, `evidence`, and `routing_policy`.
