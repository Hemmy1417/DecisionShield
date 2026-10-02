<p align="center">
  <img src="docs/assets/ds-mark.svg" width="84" height="84" alt="DecisionShield">
</p>

<h1 align="center">DecisionShield</h1>

## Thesis

**DecisionShield is a reusable GenLayer Intelligent Contract that adversarially
tests AI-powered financial decisions by adjudicating whether a bounded decision
violated an explicitly declared policy, using independently evaluated evidence
and deterministic lifecycle controls to produce machine-readable,
consensus-backed results.**

<!-- DEPLOYMENT:START -->
## Canonical deployment

[`0xc95E80E2a1bDe77A2e8aCB18fcaa374a6385cBf0`](https://explorer-studio.genlayer.com/address/0xc95E80E2a1bDe77A2e8aCB18fcaa374a6385cBf0)
on GenLayer StudioNet (chain id 61999), from commit `8f571fc`, deployed source read
back with `gen_getContractCode` and **byte-identical** to this repository.
Deployment transaction
[`0xa3a034eed9ec7c91230005474c1a861897eb1aa395025190a426c8b476057509`](https://explorer-studio.genlayer.com/tx/0xa3a034eed9ec7c91230005474c1a861897eb1aa395025190a426c8b476057509),
FINALIZED, leader execution SUCCESS. It supersedes a first deployment
(`deploy/superseded/0x99612d2d/`) - see
[`DECISION.md`](DECISION.md#the-panels-subjects).
<!-- DEPLOYMENT:END -->

## The question

> **Given a declared financial decision policy, a specific decision case, and
> independently observable evidence, did an AI-powered financial system produce a
> decision that violated one or more predefined decision constraints?**

DecisionShield is not the financial decision-maker. It approves nothing, denies
nothing, freezes nothing and moves nothing. It is an independent adjudication
layer for testing whether an AI financial system followed the rules it was
supposed to follow.

## The problem

AI now declines credit, flags fraud, scores transaction risk and screens for
compliance. When someone believes one of those decisions broke the operator's own
policy - a decline the rule forbade, a decision that leaned on a prohibited
factor, an explanation the inputs contradict, an applicant who talked the model
into an approval - the evidence is spread across a policy document, structured
inputs, the model's recorded output and its own explanation. Today the reading
is done by the operator's compliance service, an internal reviewer, or one model
call: one authority, in private.

## Why GenLayer is load-bearing

Delete GenLayer and the answer comes from the party whose system is under test,
or from one reviewer whose reading nobody can check. The question is a reading of
a prose policy against case evidence and a model's account of itself. Several
independent validators can each perform that reading on bytes they fetch
themselves, refuse a leader whose verdict is well-formed but wrong, and leave a
typed record a third system can act on.

Deterministic code owns everything else: identity, hashes, versions, bounds,
deadlines, replay protection, transitions and storage.

## Evidence roles - and the explanation

| Role | What it is |
|---|---|
| `POLICY` | the challenge's policy document, re-fetched every round against its declared sha256 |
| `CASE_INPUT` | what the AI decided on - synthetic or redacted |
| `MODEL_OUTPUT` | what it decided, as the system recorded it |
| `EXPLANATION` | the system's own account of why |
| `CORROBORATION` | an external record to check the case against |

**An AI system's explanation is a claim about its decision, never evidence for
it.** No finding a verdict rests on may be quoted from it; the decision is read
only from the recorded output; and a false explanation is its own reading, not
"contradictory evidence".

## Verdicts

```text
PENDING
  ├─ resolve → POLICY_VIOLATION_CONFIRMED   (severity: the challenge's own)
  ├─ resolve → POLICY_COMPLIANT
  ├─ resolve → INCONCLUSIVE
  ├─ resolve → EVIDENCE_UNAVAILABLE
  └─ cancel  → CANCELLED
```

`INCONCLUSIVE` and `EVIDENCE_UNAVAILABLE` are never collapsed into compliance or
violation, and **both** positive verdicts need their deciding passages quoted
from bound, non-explanation evidence.

```json
{
  "verdict": "POLICY_VIOLATION_CONFIRMED",
  "severity": "HIGH",
  "policy_compliant": false,
  "evidence_status": "EVIDENCE_REACHABLE",
  "criteria": {
    "decision_recorded": true,
    "violation_condition_met": true,
    "rule_followed": false,
    "prohibited_factor_detected": true,
    "explanation_supported": false
  }
}
```

## Lifecycle and who moves it

```
publish_challenge ──► OPEN ──(deadline)──► CLOSED
        └─ cancel_challenge (publisher, before any case) ──► CANCELLED

submit_case ──► PENDING ──resolve──► RESOLVED ──(contest window)──► finalize ──► FINAL
                  │  │                  └─ contest (tester or publisher, once)
                  │  └─ withdraw_case (tester) ──► CANCELLED
                  └─ lapse_case (anyone, after the resolve window) ──► CANCELLED
```

| Step | Who |
|---|---|
| publish / cancel a challenge | the publisher - an operator's model-risk team, an auditor, a governance body |
| submit / withdraw a case | the tester - a red team, model risk, an advocate |
| resolve, finalize, lapse | anyone; the round decides, not the caller |
| contest | the tester or the publisher, once |

## Contract surface

24 methods: 8 writes, 16 views, none payable. The views the brief names are all
there: `get_challenge`, `get_submission`, `get_verdict`,
`is_policy_violation_confirmed`, `get_policy_hash`, `get_evidence_status`,
`get_challenge_status`, `get_policy_version` - plus `get_resolution`,
`get_latest_resolution`, `get_history`, `get_actions`, `list_challenges`,
`list_submissions`, `get_stats` and `get_config`.

## Validator design

Each validator reproduces the round from its own retrieval and model call, gates
the leader's payload against its own bytes, then compares what was retrieved and
what it leads to: the verdict, the reason, and - for a positive verdict - every
criterion. Notes and quote choice may differ. [`docs/CONSENSUS.md`](docs/CONSENSUS.md).

## Financial safety, privacy, and no false guarantees

- Not a substitute for regulated decision-making, compliance review, model-risk
  management or professional oversight; no legal or regulatory certification.
- A compliant verdict does not prove a model safe; a confirmed violation does not
  prove intent; a case without one does not prove no other exists.
- Synthetic references only. Every free-text field passes a privacy guard that
  refuses email addresses and long digit runs - a heuristic, documented as such.
  No raw personal financial data is required or stored.

[`docs/SECURITY.md`](docs/SECURITY.md).

## Reuse surface

```python
answer = IDecisionShield(DS).view().is_policy_violation_confirmed(submission_id)
if answer["confirmed"] and answer["final"]:
    ...   # the consumer's own review process; DecisionShield takes no action
```

Consumers: fintech model-risk and compliance teams reading the full record; model
monitoring polling one boolean; risk, insurance and infrastructure systems
reading verdict, severity, criteria and the policy hash.
[`docs/INTEGRATION.md`](docs/INTEGRATION.md).

## Verification

<!-- VERIFIED:START -->
| Check | Result |
|---|---|
| `python -m pytest tests/direct -q` | 116 passed |
| pickling of the nondeterministic closures | checked (`direct_vm.check_pickling = True`) |
| `genvm-lint check contracts/decisionshield.py --json` (`GENVM_VERSION=v0.3.0-rc7`) | lint ok (3 checks), validation ok, 24 methods (16 view, 8 write), exit 0 |
| `ruff check .` | clean |
| `python scripts/generate_fixtures.py --check` | 16 fixture files regenerate byte for byte |
| `python scripts/mutation_check.py` | 85 mutations, **85 killed, 0 survived** |
| `python scripts/deploy_studionet.py --verify` | deployed and repository sha256 equal, 24 schema methods |
| `python -m pytest tests/integration -q` | INTEGRATION_PENDING |
| live run of record | LIVE_PENDING |

LIVE_SUMMARY_PENDING
<!-- VERIFIED:END -->

## Reviewer fast path

1. [`DECISION.md`](DECISION.md) - the specification, written before the contract,
   and what the first diagnostic pass changed.
2. [`docs/CONSENSUS.md`](docs/CONSENSUS.md) - which evidence each reading may
   quote, and what validators compare.
3. `contracts/decisionshield.py` - `_verdict_for`, `_quotable`, `_code_reason`,
   `_privacy_error`.
4. [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) - every transaction of the run of
   record.
5. `tests/direct/test_ds_adversarial.py` - the brief's adversarial matrix, one
   test at a time.

## Licence

MIT. See [`LICENSE`](LICENSE).
