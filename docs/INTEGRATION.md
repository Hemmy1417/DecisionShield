# Integration

How a model-monitoring system, a governance process or another Intelligent
Contract reads a DecisionShield verdict without reinterpreting storage.

## The consumer's interface

```python
@gl.contract_interface
class IDecisionShield:
    class View:
        def is_policy_violation_confirmed(self, submission_id: str) -> dict: ...
        def get_verdict(self, submission_id: str) -> dict: ...
        def get_policy_hash(self, challenge_id: str) -> dict: ...

    class Write:
        pass
```

A monitor gating on a confirmed violation:

```python
DS = Address("0x...")                   # the canonical deployment

answer = IDecisionShield(DS).view().is_policy_violation_confirmed(submission_id)
if answer["confirmed"] and answer["final"]:
    ...   # open a review in the consumer's own process; DecisionShield takes no action
```

A governance process checking the policy it relied on:

```python
verdict = IDecisionShield(DS).view().get_verdict(submission_id)
if verdict["policy_sha256"] != EXPECTED_POLICY_SHA256:
    raise gl.vm.UserError("[EXPECTED] that verdict was judged under a different policy")
```

No web access, no prompt, no equivalence principle, no parsing of the evidence.

## What each view answers

| Method | Returns |
|---|---|
| `is_policy_violation_confirmed(submission_id)` | `confirmed`, `final`, `verdict`, `severity` - the cheapest thing to poll |
| `get_verdict(submission_id)` | `verdict`, `reason_code`, `severity`, `policy_compliant` (true, false or null), `evidence_status`, `criteria`, `final`, the `policy_version` and `policy_sha256` it was judged under, and `resolution_id`, the round the standing verdict came from |
| `get_evidence_status(submission_id)` | per item: role, kind, status, whether it was compared; the evidence status; the markers |
| `get_submission(submission_id)` | the case as filed, the AI's explanation flagged `explanation_is_a_claim`, the evidence list and its commitment |
| `get_resolution` / `get_latest_resolution` / `get_history` | every round: each reading with the passage it quotes and its `compared` flag, whether the round was `applied`, and `leader_chosen` - the fields that are the leader's own choice rather than consensus |
| `get_challenge`, `get_policy_hash`, `get_policy_version` | the challenge as published, its definition hash, the policy document's sha256 and version |
| `get_challenge_status(challenge_id, as_of)` | whether it still accepts cases at that time |
| `get_actions(submission_id, as_of)` | what can happen next: `may_resolve` and `resolve_by` (anyone, or the tester), `resolve_rounds_left`, `may_contest` and `contest_rounds_left` per party, `may_finalize`, `may_lapse`, `may_withdraw` |
| `list_challenges`, `list_submissions`, `get_stats`, `get_config` | paging, counts, and the vocabulary: verdicts, reasons, caps and the marker phrases |

A view has no clock, so the two time-dependent views take `as_of`
(`YYYY-MM-DDTHH:MM:SSZ`); the brief's `get_challenge_status(challenge_id)` is that
view with the time made explicit. A malformed `as_of` returns `found: true,
as_of_valid: false`, never a missing record.

## The criteria object

```json
{
  "decision_recorded": true,
  "violation_condition_met": true,
  "rule_followed": false,
  "prohibited_factor_detected": true,
  "explanation_supported": false
}
```

The five keys are present from filing. Each is true, false or null (pending,
unclear, not reached, not compared, or - for prohibited factors - none
declared). For a positive verdict every validator agreed on every value. For any
other outcome only the values its reason fixed are served; the rest are `null`,
never one node's unchecked reading.

## Reading a verdict correctly

1. **`confirmed` is not `final`.** Inside its contest window a verdict can be read
   again, once by each party. Anything consequential should wait for `final`.
2. **`INCONCLUSIVE` and `EVIDENCE_UNAVAILABLE` are not compliance.** They mean no
   determination.
3. **The severity is the challenge's.** It is the severity the publisher declared
   for this violation condition, not a model's grade.
4. **A verdict is about one case.** It says nothing about the model elsewhere.
5. **`EVIDENCE_UNAVAILABLE` on a `PENDING` case is not the end.** It means the
   last round could not read the evidence; the tester can resolve again while the
   window is open. It is final only when `final` is true.
6. **`resolution_id` is the round the standing verdict came from.** A contest
   round whose evidence was unavailable is in `get_history` with
   `applied: false` and does not change the verdict.
7. **Notes, quotes and the excerpt are the leader's words.** They are grounded in
   the evidence but not compared; act on the verdict and the criteria.

## Writing, for the parties who do

| Method | Who |
|---|---|
| `publish_challenge(challenge_json)` | anyone; the sender becomes the publisher |
| `cancel_challenge(challenge_id)` | the publisher, before the first case |
| `submit_case(challenge_id, challenge_hash, policy_version, policy_sha256, subject_reference, input_summary, ai_decision, decision_explanation, claimed_violation, evidence_json)` | the tester; one per challenge, again only after a case that ended without a reading |
| `withdraw_case(submission_id)` | the tester, while pending and inside the resolve window |
| `resolve(submission_id)` | anyone for the first round; the tester for the retries after a round that could not read the evidence; five rounds at most |
| `contest(submission_id)` | the tester or the publisher, inside the contest window: one contest that is read each, three rounds each at most |
| `finalize(submission_id)` | anyone, after the contest window |
| `lapse_case(submission_id)` | anyone, after the resolve window, if no reading was reached: `CANCELLED` if nobody resolved it, `FINAL` as `EVIDENCE_UNAVAILABLE` if every round found the evidence unavailable |

`evidence_json` lists 1 to 5 items `{"url", "kind", "role", "sha256", "label"}`;
`kind` is `PINNED`, `sha256` is the digest of the bytes at `url`, `role` is
`CASE_INPUT`, `MODEL_OUTPUT`, `EXPLANATION` or `CORROBORATION`, and the
challenge's policy is always added as item `P`. Keep each document under 20,000
characters of text: a longer one cannot carry a positive verdict.

