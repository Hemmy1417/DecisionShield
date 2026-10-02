# Submission - DecisionShield

Copy-ready for the portal's Builder > Intelligent Contracts form. No addresses,
hashes or shell commands appear in the free-text fields: the contract goes only
in the evidence row the portal recognises as a GenLayer Explorer contract.

## Title

DecisionShield - adversarial policy tests for AI financial decisions

## One-line thesis

A reusable GenLayer Intelligent Contract that adjudicates whether an AI-powered
financial decision violated a policy declared in advance, from independently
evaluated evidence, and records a typed result a monitoring system reads in one
call.

<!-- PORTAL:START -->
## Portal description (983 characters, limit 1000)

An operator's model-risk team publishes a challenge: a prose policy bound to its hash, the condition that counts as a violation, prohibited factors and a severity. A tester files a case against an AI financial decision with its evidence: the inputs, the model's recorded output, its own explanation, and corroborating records. Validators fetch every document and read the policy against the case: was the decision recorded, is the violation condition met, was the rule followed, was a prohibited factor used, does the evidence support the explanation. The explanation is a claim, never evidence: no finding may be quoted from it. Code, not the model, derives POLICY_VIOLATION_CONFIRMED, POLICY_COMPLIANT, INCONCLUSIVE or EVIDENCE_UNAVAILABLE, and an injection aimed at the adjudicator stops the round. Verified with 116 Direct Mode tests, an 85-mutation sweep, GenVM lint, live integration tests, and 14 of 14 live outcomes on a StudioNet deployment byte-identical to the repository.
<!-- PORTAL:END -->

## Evidence rows

| Type | What |
|---|---|
| GitHub Repository | https://github.com/Hemmy1417/DecisionShield |
| GenLayer Explorer Contract | https://explorer-studio.genlayer.com/address/0xc95E80E2a1bDe77A2e8aCB18fcaa374a6385cBf0 |

## Reviewer fast path

1. `DECISION.md` - the specification written before the contract, and what the
   first diagnostic pass changed.
2. `docs/CONSENSUS.md` - which evidence each reading may quote, what validators
   compare, and the live findings.
3. `contracts/decisionshield.py` - `_verdict_for`, `_quotable`, `_code_reason`,
   `_privacy_error`.
4. `docs/DEPLOYMENT.md` - every transaction of the run of record, and the pass
   before it.
5. `tests/direct/test_ds_adversarial.py` - the brief's adversarial matrix.
