---
name: inference-portability-benchmark
description: Compare Kimi inference across approved runtimes and hardware while separating runtime speed, model quality, quantization effects, and protocol compatibility.
metadata:
  version: "1.0.0"
  profile: "evaluation"
---

# Inference Portability Benchmark

## Contract

**Input:** pinned model artifacts, approved runtimes, hardware manifests, fixture suite, and resource limits.

**Output:** reproducible benchmark matrix, quality deltas, protocol gaps, resource use, and deployment recommendation.

**Done:** every comparison uses equivalent prompts and reports model digest, quantization, warm-up, sampling, hardware, runtime, and raw result locations.

**Non-goals:** installing unapproved runtimes, comparing different model weights as if only the runtime changed, or accepting vendor benchmark claims as local evidence.

## Workflow

1. Record CPU, GPU, RAM, operating system, drivers, runtime version, model digest, quantization, and context settings.
2. Run warm-up separately and disclose it.
3. Measure time to first token, decode throughput, end-to-end latency, peak memory, power when available, and failure rate.
4. Run quality fixtures for instruction following, structured output, tool calls, long context, and deterministic code tasks.
5. Compare current Windows/Ollama operation first.
6. Keep Rapid-MLX and MLX-only paths marked `future_hardware` until Apple Silicon exists and the benchmark is run there.
7. Reject deployment recommendations where speed improves but required protocol or quality gates regress.

## Limits

`max_runtimes: 3`, `max_models: 1`, `max_attempts: 2` per fixture. No automatic model downloads above the approved size budget.

## Output

Return `hardware`, `artifacts`, `runtime_matrix`, `quality_matrix`, `resource_matrix`, `protocol_gaps`, and `deployment_recommendation`.
