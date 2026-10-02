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
| `get_verdict(submission_id)` | `verdict`, `reason_code`, `severity`, `policy_compliant` (true, false or null), `evidence_status`, `criteria`, `final`, and the `policy_version` and `policy_sha256` it was judged under |
| `get_evidence_status(submission_id)` | per item: role, kind, status, whether it was compared; the evidence status; the markers |
| `get_submission(submission_id)` | the case as filed, the AI's explanation flagged `explanation_is_a_claim`, the evidence list and its commitment |
| `get_resolution` / `get_latest_resolution` / `get_history` | every reading with the passage it quotes and its `compared` flag |
| `get_challenge`, `get_policy_hash`, `get_policy_version` | the challenge as published, its definition hash, the policy document's sha256 and version |
| `get_challenge_status(challenge_id, as_of)` | whether it still accepts cases at that time |
| `get_actions(submission_id, as_of)` | what can happen next, and who may do it |
| `list_challenges`, `list_submissions`, `get_stats`, `get_config` | paging, counts and the vocabulary |

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

Each is true, false or null (unclear, not reached, or - for prohibited factors -
none declared). For a positive verdict every validator agreed on every value.

## Reading a verdict correctly

1. **`confirmed` is not `final`.** Inside its contest window a verdict can be read
   again once. Anything consequential should wait for `final`.
2. **`INCONCLUSIVE` and `EVIDENCE_UNAVAILABLE` are not compliance.** They mean no
   determination.
3. **The severity is the challenge's.** It is the severity the publisher declared
   for this violation condition, not a model's grade.
4. **A verdict is about one case.** It says nothing about the model elsewhere.

## Writing, for the parties who do

| Method | Who |
|---|---|
| `publish_challenge(challenge_json)` | anyone; the sender becomes the publisher |
| `cancel_challenge(challenge_id)` | the publisher, before the first case |
| `submit_case(challenge_id, challenge_hash, policy_version, policy_sha256, subject_reference, input_summary, ai_decision, decision_explanation, claimed_violation, evidence_json)` | the tester; one per challenge |
| `withdraw_case(submission_id)` | the tester, while pending |
| `resolve(submission_id)` | anyone, inside the resolve window |
| `contest(submission_id)` | the tester or the publisher, once, inside the contest window |
| `finalize(submission_id)` | anyone, after the contest window |
| `lapse_case(submission_id)` | anyone, after the resolve window, if nobody resolved it |

`evidence_json` lists 1 to 5 items `{"url", "kind", "role", "sha256", "label"}`;
`role` is `CASE_INPUT`, `MODEL_OUTPUT`, `EXPLANATION` or `CORROBORATION`, and the
challenge's policy is always added as item `P`.
