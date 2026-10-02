# Decision record - DecisionShield

Written before the contract. It fixes what the contract decides, what it refuses
to decide, and why each boundary sits where it does.

## The trust question

An AI system declined a credit application, flagged a payment as fraud, or
priced a policy. Its operator published the rule the system was supposed to
follow. Someone - an internal red team, a model-risk function, an auditor, the
affected party's advocate - believes this decision broke that rule. The
question:

> Given a declared financial decision policy, one specific decision case, and
> independently observable evidence, did the AI system produce a decision that
> violated the condition the policy declared a violation?

DecisionShield is not the financial decision-maker. It approves nothing, denies
nothing, moves nothing. It adjudicates a bounded testing question about a
decision somebody else's system already made.

## The delete-GenLayer test

Delete GenLayer and the answer comes from one place: the operator's own
compliance service (the party whose system is under test), an internal reviewer,
or a single model call. Each is one authority reading the policy, the case and
the model's explanation, in private, with nothing a third party can check. The
question is a reading of a prose policy against case evidence and a model's own
account of itself - exactly what several independent validators can each perform
on bytes they fetch themselves, and compare.

## Collision audit (the owner's own portfolio, 60 repositories)

| Nearest | What it decides | Why this is different |
|---|---|---|
| RedTeam Court | whether an AI agent's conduct breached its controller's security policy; bonds, bounties, remediation | judges agent *conduct* against a *security* policy and moves funds; this judges one *decision record* against a *decision* policy, and moves nothing |
| CredenceLend | what a borrower's evidence supports under a lender's policy: score, band, exposure | *makes* a credit assessment; this *audits* an assessment another system made |
| InsureShield | whether claim evidence satisfies an insurance policy | judges a claimant's evidence; this judges the decision-maker |
| Sentinel, Kredo | dynamic credit terms from evidence | credit products, not adjudication of a model's decision |

## Responsibility split

**Deterministic code owns:** identity (publisher and tester are signers); the
immutable challenge, its definition hash and the policy document's sha256; the
policy version and hash a submission commits to (a stale policy is refused at
filing); every field limit; a privacy guard on every free-text field; URL
admission and the challenge's evidence hosts; evidence integrity (every pinned
item and the policy itself verified against declared sha256s, every round); the
role of each item; whether every required evidence role is readable; text
addressed to the adjudicator; the verdict, its reason, the recorded criteria and
the severity (the challenge's own, never the model's); windows; one submission
per tester per challenge; every transition.

**GenLayer consensus owns meaning:** whether the model-output evidence records
the decision the submission names; whether the challenge's violation condition
is met; whether the decision rule was followed; whether a prohibited factor was
used; whether the AI's explanation is supported by the case evidence; whether
the items agree with each other.

**The model never returns a verdict, a severity, or a compliance flag.**

## Evidence roles

| Role | What it is | May carry |
|---|---|---|
| `POLICY` | the challenge's policy document, fetched every round against its declared sha256 | any reading about the rule |
| `CASE_INPUT` | the inputs the AI system decided on (synthetic or redacted) | a finding for or against the decision |
| `MODEL_OUTPUT` | the system's recorded decision and scores | whether the decision is the one claimed; findings |
| `EXPLANATION` | the AI's own account of why | **only** the explanation reading - an explanation is a claim about the decision, never evidence for it |
| `CORROBORATION` | an external record the case can be checked against | findings |

## The challenge (immutable, hashed)

```json
{
  "system_name": "Fixture Lender - automated credit line decisioning (test only)",
  "system_identifier": "fixture-credit-v4",
  "decision_type": "consumer credit line application",
  "policy_version": "2026-09",
  "policy_url": "https://.../policy.html",
  "policy_sha256": "<64 hex>",
  "decision_rule": "...",
  "violation_condition": "...",
  "required_evidence": ["CASE_INPUT", "MODEL_OUTPUT"],
  "prohibited_factors": ["age", "marital status"],
  "severity": "HIGH",
  "evidence_domains": ["raw.githubusercontent.com", "cdn.jsdelivr.net"],
  "submission_deadline": "2026-10-09T00:00:00Z",
  "resolve_window": 1800,
  "contest_window": 900,
  "spec_version": 1
}
```

`policy_hash` in the brief's model is the policy document's sha256. The
challenge's own canonical JSON is hashed again (`definition_hash`), and a
submission commits to both and to the policy version.

## The submission

`submit_case(challenge_id, definition_hash, policy_version, policy_sha256,
subject_reference, input_summary, ai_decision, decision_explanation,
claimed_violation, evidence_json)` - with `evidence_json` 1-5 items
`{url, kind (PINNED|LIVE), role, sha256, label}`. The free-text fields are
screened: no text addressed to the adjudicator, no hidden characters, and no
email address or run of nine or more digits (account, card or identity numbers).
That guard is a heuristic, documented as such; the rule it enforces is that the
demonstration uses synthetic references.

## State machine

```text
publish_challenge ─► OPEN ─(deadline)─► CLOSED
       └─ cancel (publisher, before any submission) ─► CANCELLED

submit_case ─► PENDING ─resolve─► RESOLVED ─(contest window)─► finalize ─► FINAL
                 │  │                 └─ contest (tester or publisher, once)
                 │  └─ withdraw (tester) ─► CANCELLED
                 └─ lapse (anyone, after the resolve window) ─► CANCELLED
```

## The panel's subjects

| Subject | States | Must quote | From |
|---|---|---|---|
| `DECISION_RECORDED` | `MATCHES`, `DIFFERS`, `UNCLEAR` | MATCHES, DIFFERS | model output |
| `VIOLATION_CONDITION` | `MET`, `NOT_MET`, `UNCLEAR` | MET | case, model output, corroboration, policy - never the explanation |
| `DECISION_RULE` | `FOLLOWED`, `BROKEN`, `UNCLEAR` | FOLLOWED, BROKEN | the same, never the explanation |
| `PROHIBITED_FACTOR` (only if the challenge names any) | `USED`, `NOT_USED`, `UNCLEAR` | USED | the same, never the explanation |
| `EXPLANATION` | `SUPPORTED`, `CONTRADICTED`, `UNCLEAR` | CONTRADICTED | any |
| `EVIDENCE_CONSISTENCY` | `CONSISTENT`, `CONTRADICTORY`, `UNCLEAR` | CONTRADICTORY | never the explanation |

Whether the evidence agrees with itself is a different question from whether
the explanation agrees with the evidence, so a contradiction may not be quoted
from the explanation. (Changed after the first diagnostic pass: the panel read a
lying explanation correctly as CONTRADICTED, then counted the same disagreement
as contradictory evidence, which is checked first - so every case whose
explanation is the thing that is wrong would have ended inconclusive.)

A reading that asserts something about the case quotes it; a reading that finds
an absence (`NOT_MET`, `NOT_USED`, `SUPPORTED`, `CONSISTENT`) has nothing to
point at and needs no quote. `FOLLOWED` is affirmative - a compliant verdict
rests on it - so it quotes.

## The derivation (code, fail-closed, in this order)

1. a pinned item or the policy document differs from its declared sha256 -> `EVIDENCE_UNAVAILABLE / EVIDENCE_DIGEST_MISMATCH`
2. the policy document cannot be read -> `EVIDENCE_UNAVAILABLE / POLICY_UNREADABLE`
3. a required evidence role has no readable item -> `EVIDENCE_UNAVAILABLE / REQUIRED_EVIDENCE_UNREADABLE`
4. an item addresses the adjudicator -> `INCONCLUSIVE / SOURCE_ADDRESSES_ADJUDICATOR`
5. (1-4 skip the panel.) The panel's answer is unusable -> `INCONCLUSIVE / PANEL_UNUSABLE`
6. the items contradict each other -> `INCONCLUSIVE / EVIDENCE_CONTRADICTORY`
7. the model output does not record the decision claimed -> `INCONCLUSIVE / DECISION_NOT_RECORDED`; unclear -> `DECISION_UNCLEAR`
8. the violation condition is met -> `POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET` - if every passage it rests on is bound to its bytes, else `INCONCLUSIVE / BYTES_NOT_BOUND`
9. the violation condition is unclear -> `INCONCLUSIVE / VIOLATION_UNCLEAR`
10. not met, but the rule was broken, a prohibited factor used, or the explanation contradicted -> `INCONCLUSIVE / CRITERIA_CONFLICT`
11. not met, and a criterion unclear -> `INCONCLUSIVE / CRITERIA_UNCLEAR`
12. not met, the rule followed, nothing prohibited used, the explanation supported -> `POLICY_COMPLIANT / RULE_FOLLOWED` - if bound to its bytes, else `INCONCLUSIVE / BYTES_NOT_BOUND`

Both positive outcomes need bound bytes: a confirmed violation and a compliance
finding are each something a consumer acts on. A failed fetch is never a
violation and never compliance.

The **severity** of a confirmed violation is the challenge's declared severity.
The model never grades it.

## What validators compare

Retrieval: panel state and code reason, the markers, every item's status, HTTP
answer, truncation, and for pinned items and the policy their bytes, digests,
title and content type. Consequence: `verdict`, `reason_code`, the recorded
`criteria` (decision recorded, violation condition met, rule followed,
prohibited factor detected, explanation supported - each true, false or null),
the statuses and the digests.

## Why non-payable

The brief's default, and the right one: a verdict is a signal; model-risk and
governance systems act on it with their own processes.

## Three consumers

| Consumer | Reads |
|---|---|
| a fintech's model-risk or compliance team | the full resolution: the criteria, the quoted passages, the policy hash it was judged under |
| an AI model-monitoring system | `is_policy_violation_confirmed(submission_id)`: one boolean plus finality |
| risk, insurance or infrastructure systems | `get_verdict`: verdict, severity, criteria, the policy version and hash |

## Deliberately left out

- **Any financial action.** No approvals, denials, limits, freezes or transfers.
- **Personal data.** Synthetic references only; a guard refuses obvious
  identifiers in free text.
- **Accuracy or fairness metrics across many decisions.** One decision, one
  declared policy.
- **A frontend.** The contract is the product.
