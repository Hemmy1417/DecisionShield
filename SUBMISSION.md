# Submission - DecisionShield

Copy-ready for the portal's Builder > Intelligent Contracts form. No addresses,
hashes or shell commands appear in the free-text fields: the contract goes only
in the evidence row the portal recognises as a GenLayer Explorer contract.

| Field | Value |
|---|---|
| Category | AI-powered financial systems / AI risk decisioning / adversarial testing (portal: Builder > Intelligent Contracts) |
| Title | DecisionShield - adversarial policy tests for AI financial decisions |
| One-line thesis | A reusable GenLayer Intelligent Contract that adjudicates whether an AI-powered financial decision violated a policy declared in advance, from independently evaluated evidence, and records a typed result a monitoring system reads in one call. |
| Repository | https://github.com/Hemmy1417/DecisionShield |
| Canonical StudioNet address | `0x8E2c66279fB5Fa0Ab6867573407aeA5787Baf467` |
| Explorer URL | https://explorer-studio.genlayer.com/address/0x8E2c66279fB5Fa0Ab6867573407aeA5787Baf467 |
| Deployment tx | `0x131cdb62f0a0203c816d2b2d96616d2066101d4d08e23913faeda7480decc262` - FINALIZED, leader SUCCESS |
| Deployment source | commit `0fca5ad`, `contracts/decisionshield.py`; deployed source byte-identical to `main` |
| Why GenLayer is required | the verdict rests on a reading of a prose policy against case evidence and the AI's own explanation; without consensus that reading comes from the party under test or one unverifiable reviewer |
| Consensus mechanism | custom `gl.vm.run_nondet_unsafe`: every validator re-fetches the pinned bytes, re-reads, gates the leader's payload against its own texts, and compares the verdict, reason, every criterion of a positive verdict, each item's status and each pinned digest; notes and quote choice may differ |
| Deterministic responsibilities | identity, hashes, versions, URL admission, privacy guard, replay and per-tester caps, deadlines and windows, digest checks, the marker scan, code reasons, quote grounding, the verdict derivation, contest, finality, lapse, bounded storage |
| Failure policy | fail closed: a failed fetch, a digest mismatch, an unreadable policy or required role is `EVIDENCE_UNAVAILABLE` and leaves the case open to be read again; contradictory or unclear evidence, a panel failure, unbound bytes or text addressed to the adjudicator is `INCONCLUSIVE`; neither is ever compliance or violation |
| Reuse surface | `is_policy_violation_confirmed(submission_id)` returns verdict, severity, confirmed and final; `get_verdict` adds the criteria and policy hash - no web, prompt or parsing needed |
| Test results | 139 Direct Mode tests with pickling checks; 110-mutation sweep, 110 killed; a read-only adversarial review whose findings are all fixed and pinned; GenVM lint and SDK validation ok; 9 StudioNet integration tests passed (1 opt-in live-write test skipped), each also run alone |
| Live evidence | run of record: 39 transactions, 16 of 16 outcomes held, 11 of 11 refusals refused - success, negative and lifecycle paths, every transaction linked in `docs/DEPLOYMENT.md` |
| Limitations | not legal or regulatory certification; one decision against one policy; honest-majority assumption; evidence hosts can go down (never a verdict); marker scan and privacy guard are heuristics; StudioNet, not a production audit |

<!-- PORTAL:START -->
## Portal description (994 characters, limit 1000)

An operator's model-risk team publishes a challenge: a prose policy bound to its hash, the condition that counts as a violation, prohibited factors and a severity. A tester files a case against an AI financial decision with its evidence: the inputs, the model's recorded output, its own explanation, and corroborating records. Validators fetch every document and read the policy against the case: was the decision recorded, is the violation condition met, was the rule followed, was a prohibited factor used, does the evidence support the explanation. The explanation is a claim, never evidence: no finding may be quoted from it. Code, not the model, derives POLICY_VIOLATION_CONFIRMED, POLICY_COMPLIANT, INCONCLUSIVE or EVIDENCE_UNAVAILABLE, and an injection aimed at the adjudicator stops the round. Verified with 139 Direct Mode tests, a 110-mutation sweep, an adversarial review, live integration tests, and 16 of 16 live outcomes on a StudioNet deployment byte-identical to the repository.
<!-- PORTAL:END -->

## Evidence rows

| Type | What |
|---|---|
| GitHub Repository | https://github.com/Hemmy1417/DecisionShield |
| GenLayer Explorer Contract | https://explorer-studio.genlayer.com/address/0x8E2c66279fB5Fa0Ab6867573407aeA5787Baf467 |

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
   diagnostic passes and the adversarial review changed.
2. `docs/CONSENSUS.md` - which evidence each reading may quote, what validators
   compare, and the live findings.
3. `contracts/decisionshield.py` - `_verdict_for`, `_quotable`, `_code_reason`,
   `_privacy_error`.
4. `docs/DEPLOYMENT.md` - every transaction of the run of record, and the five
   passes before it.
5. `tests/direct/test_ds_adversarial.py` - the brief's adversarial matrix.
