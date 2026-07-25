---
name: kimi-protocol-parity-lab
description: Reproduce and compare Kimi, OpenAI-compatible, and Anthropic-compatible request, streaming, tool-call, error, and structured-output contracts using pinned fixtures.
metadata:
  version: "1.0.0"
  profile: "evaluation"
---

# Kimi Protocol Parity Lab

## Contract

**Input:** provider endpoint, pinned model identity, protocol mode, fixture set, and declared capabilities.

**Output:** protocol matrix, raw evidence paths, incompatibilities, safe adapter behavior, and unsupported-feature decisions.

**Done:** every claimed compatibility feature has a positive fixture, a negative fixture, and an observed termination/error contract.

**Non-goals:** inferring support from model names, sending secrets, enabling a provider, or rewriting production routing.

## Workflow

1. Record endpoint, model identifier, provider version, SDK version, and runtime timestamp.
2. Run deterministic fixtures for basic text, streaming, stop reasons, structured output, tool calls, malformed arguments, cancellation, and rate-limit behavior.
3. Preserve raw request and response bodies with secrets redacted.
4. Compare semantic and wire-level behavior across protocols.
5. Classify each feature as `supported`, `supported_with_adapter`, `unsupported`, `unstable`, or `not_tested`.
6. Generate the narrowest adapter rules; reject silent parameter dropping for consequential settings.
7. Require an independent rerun before changing a production alias.

## Limits

`max_attempts: 2` per fixture. No retry on deterministic validation errors. Maximum one provider and one model per run unless the user requests a comparison.

## Output

Return `environment`, `feature_matrix`, `raw_evidence`, `adapter_rules`, `failures`, and `routing_recommendation`.
