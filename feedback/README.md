
# Review feedback

Append one JSON object per reviewed proposal to `decisions.jsonl`:

```json
{"repository":"owner/repo","owner":"owner","categories":["mcp_server"],"decision":"accepted","reviewed_at":"2026-07-23T00:00:00Z"}
```

Allowed decisions are `accepted` and `rejected`. The learning agent derives a bounded
score adjustment between -10 and +10. Feedback can never modify code, security policy,
network permissions, or activation state.
