# Submission - DecisionShield

Copy-ready for the portal's Builder > Intelligent Contracts form. No addresses,
hashes or shell commands appear in the free-text fields: the contract goes only
in the evidence row the portal recognises as a GenLayer Explorer contract.

## Category

AI-powered financial systems / AI risk decisioning / adversarial testing (portal: Builder > Intelligent Contracts)

## Title

DecisionShield - adversarial policy tests for AI financial decisions

## One-line thesis

A reusable GenLayer Intelligent Contract that adjudicates whether an AI-powered financial decision violated a policy declared in advance, from independently evaluated evidence, and records a typed result a monitoring system reads in one call.

## Repository

https://github.com/Hemmy1417/DecisionShield

## Canonical StudioNet address

`0x2Eeb9e62Cf44654a90cB7263eD4620b0bb3422E3`

## Explorer URL

https://explorer-studio.genlayer.com/address/0x2Eeb9e62Cf44654a90cB7263eD4620b0bb3422E3

## Deployment tx

`0x5d61744aee027560d56c42f5d0716aa225b29b35f5f15d962db2caff44fdfc48` - FINALIZED, leader SUCCESS

## Deployment source

commit `913ccdb`, `contracts/decisionshield.py`, version 0.4.1; deployed source byte-identical to `main`

## Why GenLayer is required

the verdict rests on a reading of a prose policy against case evidence and the AI's own explanation; without consensus that reading comes from the party under test or one unverifiable reviewer

## Consensus mechanism

custom `gl.vm.run_nondet_unsafe`: every validator re-fetches the pinned bytes, re-reads, gates the leader's payload against its own text, and compares the verdict, reason, every criterion of a positive verdict, what each node could do with each item, and each digest; notes, quote choice and HTTP details may differ

## Deterministic responsibilities

identity, hashes, versions, URL admission, pinning, privacy guard, replay and per-tester caps, deadlines and windows, digest checks, how bytes become the panel's text, the marker scan, code reasons, quote grounding, the verdict derivation, retries, each party's contest, finality, lapse, bounded storage

## Failure policy

fail closed: a failed fetch, a digest mismatch, an unreadable policy or any unreadable declared item is `EVIDENCE_UNAVAILABLE`, leaves the case open and never replaces a reading; contradictory or unclear evidence, a panel failure, a truncated item or text addressed to the adjudicator is `INCONCLUSIVE`; neither is ever compliance or violation

## Reuse surface

`is_policy_violation_confirmed(submission_id)` returns verdict, severity, confirmed and final; `get_verdict` adds the criteria and policy hash - no web, prompt or parsing needed

## Test results

184 Direct Mode tests with pickling checks; 166-mutation sweep, 166 killed; four read-only adversarial reviews, every finding fixed and pinned, the fourth with nothing on the verdict path; GenVM lint and SDK validation ok; StudioNet integration tests 9 passed, 1 skipped, each also run alone

## Live evidence

run of record: 38 transactions, 15 of 15 outcomes held, 12 of 12 refusals refused for their intended reasons - success, negative and lifecycle paths, every transaction linked in `docs/DEPLOYMENT.md`

## Limitations

not legal or regulatory certification; one decision against one policy; honest-majority assumption; a host can cause an outage (recorded, never a verdict) and delay finality by a bounded number of windows; the marker scan and privacy guard are heuristics; the panel reads the pinned bytes' text by a fixed rule, not as a browser; StudioNet, not an independent production audit

<!-- PORTAL:START -->
## Portal description (963 characters, limit 1000)

An operator's model-risk team publishes a challenge: a prose policy bound to its hash, the condition that counts as a violation, prohibited factors and a severity. A tester files a case against an AI financial decision: the inputs, the model's recorded output, its own explanation and corroborating records, each pinned to its hash. Validators fetch every document and read the policy against the case: was the decision recorded, is the violation condition met, was the rule followed, was a prohibited factor used, does the evidence support the explanation. The explanation is a claim, never evidence. Code, not the model, derives POLICY_VIOLATION_CONFIRMED, POLICY_COMPLIANT, INCONCLUSIVE or EVIDENCE_UNAVAILABLE; an outage can never end a case or replace a reading. Verified with 184 Direct Mode tests, a 166-mutation sweep, four adversarial reviews, live integration tests, and 15 of 15 live outcomes on a StudioNet deployment byte-identical to the repository.
<!-- PORTAL:END -->

## Evidence rows

| Type | What |
|---|---|
| GitHub Repository | https://github.com/Hemmy1417/DecisionShield |
| GenLayer Explorer Contract | https://explorer-studio.genlayer.com/address/0x2Eeb9e62Cf44654a90cB7263eD4620b0bb3422E3 |

## Reviewer fast path

```bash
git clone https://github.com/Hemmy1417/DecisionShield.git && cd DecisionShield
pip install -r requirements-test.txt
python scripts/fetch_genvm_bundle.py
python -m pytest tests/direct -q
python scripts/deploy_studionet.py --verify
python -m pytest tests/integration -q
```

1. `DECISION.md` - the specification written before the contract, and what the
   diagnostic passes and four adversarial reviews changed.
2. `docs/CONSENSUS.md` - which evidence each reading may quote, what validators
   compare, and the live findings.
3. `contracts/decisionshield.py` - `_verdict_for`, `_code_reason`, `_quotable`,
   `_looks_html`, `_strip_markup`, `_marker_hits_in`.
4. `docs/DEPLOYMENT.md` - every transaction of the run of record, and the seven
   passes before it.
5. `tests/direct/test_ds_adversarial.py` - the brief's adversarial matrix;
   `tests/direct/test_ds_review.py` and the three files after it - what each
   review found.
