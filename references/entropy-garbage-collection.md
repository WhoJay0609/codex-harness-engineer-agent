# Entropy And Garbage Collection

Use this reference when the harness or generated code starts drifting.

## What To Scan

- Repeated helper functions that should become shared utilities.
- Ad hoc fallback paths that hide invalid state.
- Guess-based parsing of external data instead of boundary validation.
- Outdated docs that contradict code behavior.
- Test-only assumptions leaking into production flow.
- Large files or mixed responsibilities that reduce agent readability.
- Skill allowlists that grew without recorded reasons.
- Subagents that stay active after their evidence is stale.

## Garbage Collection Loop

1. Scan artifacts, code, docs, and previous failures.
2. Rank drift by risk and frequency.
3. Convert recurring drift into a mechanical gate when possible.
4. Open a small cleanup task or run a bounded refactor.
5. Verify that the cleanup improves future agent readability.
6. Record the rule or exception in the repo record system.

## Quality Score

Track coarse scores per domain or harness area:

```json
{
  "area": "agent-trace",
  "score": 4,
  "max_score": 5,
  "gaps": ["missing handoff summaries for skipped escalations"],
  "next_gc_task": "require rejected_reason when called_multi_agent=false"
}
```

The goal is continuous small cleanup, not large periodic rewrites.
