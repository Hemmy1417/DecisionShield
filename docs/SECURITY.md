# Security, privacy and the financial safety boundary

## What this contract is not

DecisionShield does **not** approve or deny credit, freeze accounts, liquidate
positions, move customer funds, determine investment suitability, set rates,
execute trades or make any regulated financial decision. It holds no funds and no
method is payable. It adjudicates a predefined testing question about a decision
another system already made.

It is an adversarial testing and governance primitive. It is not a substitute for
regulated decision-making, compliance review, model-risk management or
professional oversight, and it provides no legal or regulatory certification.

## What a verdict means - and does not

- `POLICY_COMPLIANT` means this case, on this evidence, met the declared rule.
  It does **not** prove the model is safe, fair or correct elsewhere.
- `POLICY_VIOLATION_CONFIRMED` means this case met the challenge's declared
  violation condition on bound evidence. It does **not** prove intent, and a case
  without a confirmed violation does not prove no other violation exists.
- `INCONCLUSIVE` and `EVIDENCE_UNAVAILABLE` mean no determination - never
  compliance, never violation.

## Assets

| Asset | Why it is worth attacking |
|---|---|
| a confirmed violation | it triggers review, remediation or disclosure; a false one harms the operator under test |
| a compliance verdict | it can be cited as proof a decision was sound; a false one buries a real violation |
| the challenge and its policy | if either could change after a case was filed, the question could be rewritten around the answer |

## Actors

| Actor | Can | Cannot |
|---|---|---|
| publisher (operator, auditor, governance body) | publish a challenge; cancel it before any case; contest a verdict once | change a published challenge or its policy; cancel once a case exists; influence a reading |
| tester (red team, model risk, an advocate) | file one case per challenge; withdraw before resolution; contest once | file twice, cite a host the challenge did not name, change evidence after filing |
| keeper (anyone) | resolve, finalise, lapse | change any outcome |
| validators | reproduce the round and refuse the leader | write a verdict; code derives it |

## Input attacks

**The AI's explanation as evidence.** An explanation is the system's claim about
its own decision. A finding a verdict rests on can never be quoted from an
`EXPLANATION` item, and the decision itself is read only from the model's
recorded output.

**Prompt injection aimed at the adjudicator.** Every document is scanned in code -
visible text, markup and attributes, title - with hidden characters, soft hyphens,
numeric entities and tag or comment splits undone. Text addressed to the
adjudicator stops the round as `SOURCE_ADDRESSES_ADJUDICATOR`. Every free-text
field of the challenge and the case is screened the same way at write time.

**Injection aimed at the financial AI** is the subject of an adversarial-input
case, not an attack on this panel. The marker list is narrow on purpose, so such
a case is adjudicated rather than silenced.

**Swapping a document.** The policy's sha256 is fixed in the challenge and each
pinned item's at filing; both are checked on every retrieval, in every round.
Different bytes are `EVIDENCE_DIGEST_MISMATCH`, and a contest cannot bring better
evidence.

**A stale policy.** A case commits to the challenge hash, the policy version and
the policy document's sha256; any mismatch is refused at filing.

**Unbound evidence.** A `LIVE` item has no digest; neither positive verdict may
rest on one.

**Fabricated or spliced support**, **malformed model output**, **replay** (one case
per tester per challenge, enforced on `challenge_id + tester`), **expired
challenges**, **double resolution** and **unauthorised mutation** are each refused
in code; `tests/direct/test_ds_adversarial.py` works through them one at a time.

## Privacy and data minimisation

- Cases use **synthetic references**. No raw personal financial record is required
  or wanted on chain; evidence is referenced by URL and sha256, and the
  demonstration data is synthetic and marked so in every document.
- Every free-text field - and every label and challenge text field - passes a
  **privacy guard** that refuses an email address or a run of nine or more digits
  (dashes allowed, so a phone number in the usual form is caught). It is a
  heuristic that catches the obvious mistakes, not a privacy guarantee: a spaced
  card number, a name or an address would pass it. The rule it enforces is that
  only synthetic or redacted data goes on chain.
- No secret, credential, key or customer record is stored in the repository;
  signing keys live in a gitignored `.data/` directory and are never printed.

## Fail-closed policy

Both positive outcomes are guarded the same way: a confirmed violation and a
compliance finding each need the readings they rest on quoted from bound,
non-explanation evidence, and every other branch is `INCONCLUSIVE` or
`EVIDENCE_UNAVAILABLE`. A rule followed with a contradicted explanation is
`CRITERIA_CONFLICT`, not compliance: a system that gives a false reason for a
lawful decision does not get a compliance stamp.

## Limitations

- One decision, one declared policy: no statement about accuracy or fairness
  across many decisions.
- The readings are model judgements; where honest models split, nothing is stored.
- Public-source evidence is only as strong as the hosts a challenge names.
- One contest per case, for whichever party uses it first.
- Identity is a wallet; the per-wallet cap bounds abuse, it does not prevent it.
