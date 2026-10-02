---
name: okr-cycle
description: Create, review, check in, or close an approval-gated OKR cycle. Use for actual OKR lifecycle work, not generic goal-setting explanations or employee evaluation.
---

# OKR Cycle

Guide an OKR from incomplete context to evidence-backed operation without choosing strategy on the user's behalf.

## Invariants

1. Ask for missing information before advancing. Prefer one primary question at a time unless the user asks for a batch.
2. Never invent baselines, targets, owners, evidence, approvals, or progress. Record unavailable facts as `UNVERIFIED` or `UNASSIGNED`.
3. Keep Objective, Key Results, and Initiatives distinct. Objectives express the desired state, KRs provide outcome evidence, and Initiatives are proposed actions.
4. A draft may contain unknowns, but only a validator-clean document can advance beyond `INCOMPLETE`.
5. Do not set `ACTIVE` or materially change an active target without unambiguous human approval referencing the current proposal.
6. Do not use OKRs as the sole basis for compensation, personnel ratings, or disciplinary decisions.
7. Preserve evidence and decisions in the canonical JSON file. Do not silently rewrite history.

## Route

Read only the reference needed for the current request:

- For creating, resuming, revising, or reviewing an OKR, read [references/setting.md](references/setting.md).
- For an `ACTIVE` OKR check-in, read [references/checkin.md](references/checkin.md).
- For period-end scoring and reflection, read [references/closing.md](references/closing.md).

For each new OKR set, copy [assets/okr-template.json](assets/okr-template.json) to `okrs/<period>/<id>.json`. Use one file for one scope and period. Do not edit the asset in place.

## State model

Use these transitions only:

```text
INCOMPLETE
  -> READY_FOR_REVIEW
  -> AWAITING_HUMAN_APPROVAL
  -> ACTIVE
  -> CLOSED
```

Move backward when review reveals missing or invalid information. Record every transition in `history` with an ISO 8601 timestamp, actor, reason, and previous/new state.

Before any forward transition, run:

```bash
python3 .codex/skills/okr-cycle/scripts/validate_okr.py <okr-json>
```

The validator is a deterministic gate, not proof that the strategy is good. Retain the qualitative review and human approval steps.

## Approval boundary

Treat phrases such as "検討します", "よさそう", or a request for another revision as feedback, not approval. Before activation, summarize the exact Objective/KRs, unresolved assumptions, and material risks, then ask for approval. Record approval only after a clear affirmative response.

For active target changes, show the old and new values, reason, expected interpretation impact, and whether historical comparability is preserved. Obtain approval before editing the target.

## Response contract

At each turn, state:

- current state;
- what was confirmed;
- what remains missing or unverified;
- the next single decision or question.

Do not claim that an OKR is valid, approved, active, or complete unless the corresponding JSON state and evidence support that claim.
