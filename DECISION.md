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

The nearest repositories are described by what they do, not named.

| Nearest | What it decides | Why this is different |
|---|---|---|
| an agent-conduct court | whether an AI agent's conduct breached its controller's security policy; bonds, bounties, remediation | judges agent *conduct* against a *security* policy and moves funds; this judges one *decision record* against a *decision* policy, and moves nothing |
| a credit-assessment contract | what a borrower's evidence supports under a lender's policy: score, band, exposure | *makes* a credit assessment; this *audits* an assessment another system made |
| an insurance-claims contract | whether claim evidence satisfies an insurance policy | judges a claimant's evidence; this judges the decision-maker |
| two credit products | dynamic credit terms from evidence | credit products, not adjudication of a model's decision |

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

The brief's policy hash is the policy document's sha256, `policy_sha256`. The
challenge's own canonical JSON is hashed again (`definition_hash`), and a
submission commits to both and to the policy version.

How the brief's suggested fields map: `deadline` is `submission_deadline`;
`status` is stored beside the definition, not inside it, so the hash never
changes; the brief's evidence URLs and evidence digest are the `evidence_json` items,
each with its own `sha256`, plus `evidence_commitment`, the sha256 of the whole
numbered list; `submitted_at` is the transaction time of the filing.

## The submission

`submit_case(challenge_id, challenge_hash, policy_version, policy_sha256,
subject_reference, input_summary, ai_decision, decision_explanation,
claimed_violation, evidence_json)` - with `evidence_json` 1-5 items
`{url, kind, role, sha256, label}`.

**Every item is pinned.** `kind` must be `PINNED` and `sha256` the digest of the
bytes at `url`; no two items may declare the same bytes, and no URL may carry an
email address. An item nobody pinned would be read by the panel all the same,
and its host could change it between rounds, so a case may not declare one under
any role.

The free-text fields, the labels, the challenge's text fields and its prohibited
factors are screened: no text addressed to the adjudicator (read in the same
decoded form as evidence), no hidden or unencodable characters, and no email
address, run of nine or more digits, or digits grouped like a phone, card or
social-security number. That guard is a heuristic, documented as such; the rule
it enforces is that the demonstration uses synthetic references.

A tester files one case per challenge. They may file again only once that case
ended without a reading: withdrawn, lapsed, or final as `EVIDENCE_UNAVAILABLE`.

## State machine

```text
publish_challenge ─► OPEN ─(deadline)─► CLOSED
       └─ cancel (publisher, before any submission) ─► CANCELLED

submit_case ─► PENDING ─resolve─► RESOLVED ─(contest window)─► finalize ─► FINAL
              │ ▲  │ │               └─ contest: one read contest per party;
              │ └──┘ │                  every contest round restarts the window
              │  resolve with evidence unavailable: recorded, stays PENDING
              │  (at most 5 resolve rounds; after the first, the tester's)
              │      └─ withdraw (tester, inside the window) ─► CANCELLED
              └─ lapse (anyone, after the resolve window)
                   ├─ never read          ─► CANCELLED / LAPSED
                   └─ evidence unavailable ─► FINAL / EVIDENCE_UNAVAILABLE
```

**Unavailable evidence never ends a case early, and never replaces a reading.**
A resolve round whose evidence cannot be read is recorded and the case stays
`PENDING`. The first round is anyone's to ask for; the retries, up to five rounds
in all, are the tester's, so nobody else can spend them while a host is down.
Only when the window passes does the outage become final - and then the tester
may file again.

**Each party has its own contest.** The tester and the publisher each have one
contest that is read, and neither can spend the other's: a party that contests a
verdict in its own favour uses up only its own. A contest round whose evidence
cannot be read is recorded with `applied: false`; the standing verdict stays and
the contest is not spent. Each party may ask for at most three contest rounds.
Every contest round restarts the contest window, so an outage cannot run out
the other party's contest and a contest read in the window's last second still
leaves the other party time to answer. Finality can therefore be delayed, but
only by a bounded number of windows.

## The panel's subjects

| Subject | States | Must quote | From |
|---|---|---|---|
| `DECISION_RECORDED` | `MATCHES`, `DIFFERS`, `UNCLEAR` | MATCHES, DIFFERS | model output |
| `VIOLATION_CONDITION` | `MET`, `NOT_MET`, `UNCLEAR` | MET | case, model output, corroboration, policy - never the explanation |
| `DECISION_RULE` | `FOLLOWED`, `BROKEN`, `UNCLEAR` | FOLLOWED, BROKEN | the same, never the explanation |
| `PROHIBITED_FACTOR` (only if the challenge names any) | `USED`, `NOT_USED`, `UNCLEAR` | USED | the same, never the explanation |
| `EXPLANATION` | `SUPPORTED`, `CONTRADICTED`, `UNCLEAR` | CONTRADICTED | any |
| `EVIDENCE_CONSISTENCY` | `CONSISTENT`, `CONTRADICTORY`, `UNCLEAR` | CONTRADICTORY | two different items, never the explanation |

Whether the evidence agrees with itself is a different question from whether
the explanation agrees with the evidence, so a contradiction may not be quoted
from the explanation. (Changed after the first diagnostic pass: the panel read a
lying explanation correctly as CONTRADICTED, then counted the same disagreement
as contradictory evidence, which is checked first - so every case whose
explanation is the thing that is wrong would have ended inconclusive.)

Nor is a wrong decision a contradiction. Inputs that qualify for approval and an
output that records a decline are both true records of what happened; that they
do not fit the policy is the violation, read by the subjects after this one. A
contradiction is two different items giving different values for the same fact,
and the reading must quote both items. (Changed after the fifth diagnostic pass:
a contest's second panel called exactly that pair contradictory and overturned a
confirmed violation.)

A reading that asserts something about the case quotes it; a reading that finds
an absence (`NOT_MET`, `NOT_USED`, `SUPPORTED`, `CONSISTENT`) has nothing to
point at and needs no quote. `FOLLOWED` is affirmative - a compliant verdict
rests on it - so it quotes.

## The derivation (code, fail-closed, in this order)

1. a pinned item or the policy document differs from its declared sha256 -> `EVIDENCE_UNAVAILABLE / EVIDENCE_DIGEST_MISMATCH`
2. the policy document cannot be read -> `EVIDENCE_UNAVAILABLE / POLICY_UNREADABLE`
3. a required evidence role has no readable item, **or any item the case declared cannot be read** -> `EVIDENCE_UNAVAILABLE / REQUIRED_EVIDENCE_UNREADABLE`
4. an item addresses the adjudicator -> `INCONCLUSIVE / SOURCE_ADDRESSES_ADJUDICATOR`
5. (1-4 skip the panel.) The panel's answer is unusable -> `INCONCLUSIVE / PANEL_UNUSABLE`
6. the items contradict each other -> `INCONCLUSIVE / EVIDENCE_CONTRADICTORY`; unclear -> `CONSISTENCY_UNCLEAR`
7. the model output does not record the decision claimed -> `INCONCLUSIVE / DECISION_NOT_RECORDED`; unclear -> `DECISION_UNCLEAR`
8. the violation condition is met -> `POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET` - unless an item was read only in part, then `INCONCLUSIVE / EVIDENCE_TRUNCATED`
9. the violation condition is unclear -> `INCONCLUSIVE / VIOLATION_UNCLEAR`
10. not met, but the rule was broken, a prohibited factor used, or the explanation contradicted -> `INCONCLUSIVE / CRITERIA_CONFLICT`
11. not met, and a criterion unclear -> `INCONCLUSIVE / CRITERIA_UNCLEAR`
12. not met, the rule followed, nothing prohibited used, the explanation supported -> `POLICY_COMPLIANT / RULE_FOLLOWED` - unless an item was read only in part, then `INCONCLUSIVE / EVIDENCE_TRUNCATED`

Step 3 is what keeps a host from choosing which of its own records the panel
sees: every item a case declares is part of the case, and one that is down makes
the round unavailable rather than letting the rest decide it.

Both positive outcomes need the whole of every document. The panel reads at
most 20,000 characters of an item (200,000 bytes are fetched); a longer one is
`PARTIAL`, its reading is recorded, and no positive verdict rests on it, because
the deciding passage may lie past the cap. A publisher whose policy is longer
publishes the governing section as its own document. `BYTES_NOT_BOUND` remains
in the vocabulary as the guard behind the filing rule: if an unpinned item ever
reached a round, neither positive verdict would be derived.

A failed fetch is never a violation and never compliance. The **severity** of a
confirmed violation is the challenge's declared severity. The model never
grades it.

## What validators compare

Retrieval: panel state and code reason, the markers, and for every item what a
node could do with it - read it whole, read it in part, find other bytes than
were pinned, or not read it - plus its byte count, raw sha256, text digest and
title. Whether a failed fetch was a 502, a 503 or a timeout is not compared:
honest nodes see different failures during one outage, and it decides nothing.
Consequence: `verdict`, `reason_code`, the `criteria` of a positive verdict
(decision recorded, violation condition met, rule followed, prohibited factor
detected, explanation supported), those status classes and the digests.

What a consumer is served follows what was compared. A positive verdict
compares every criterion, so every criterion is served. Any other outcome
compares only its verdict and reason, which fix the readings up to the one the
derivation stopped at; every other criterion is served as `null`, never as a
leader's unchecked claim. The full readings stay in the resolution record, each
with its `compared` flag, and each record lists the fields that are the leader's
own choice (`leader_chosen`): the excerpt, the notes, which passages were quoted,
and the HTTP details of each fetch.

## Why non-payable

The brief's default, and the right one: a verdict is a signal; model-risk and
governance systems act on it with their own processes.

## Three consumers

| Consumer | Reads |
|---|---|
| a fintech's model-risk or compliance team | the full resolution: the criteria, the quoted passages, the policy hash it was judged under |
| an AI model-monitoring system | `is_policy_violation_confirmed(submission_id)`: one boolean plus finality |
| risk, insurance or infrastructure systems | `get_verdict`: verdict, severity, criteria, the policy version and hash |

## What the adversarial review changed

The contract was read four times by a fresh, read-only adversary, each time
after the previous round's fixes, and each finding was proved with a throwaway
test before it was accepted. The first three rounds found real defects on the
verdict path; the fourth found none there. Every fix has its own test and its
own mutation (`tests/direct/test_ds_review.py`, `test_ds_second_review.py`,
`test_ds_third_review.py`, `test_ds_fourth_review.py`).

| Finding | Fix |
|---|---|
| the operator under test could bury a case: take its policy host down, resolve, spend the one contest during the outage, and finalize | unavailable evidence leaves the case `PENDING`; an unavailable contest round is not applied and spends nothing; a case that ends without a reading may be filed again |
| the same, by taking down only one pinned item - the one record that shows the violation | any declared item that cannot be read makes the round unavailable |
| a positive verdict could rest on an unpinned input, first by quoting only the pinned policy, then by labelling the input an "explanation" | every item a case declares is pinned; an unpinned one is refused at filing |
| the favoured party could contest its own verdict and so spend the only contest; an outage could run the contest window out | one read contest per party; every contest round restarts the window; rounds are capped per party |
| anyone could keep resolving an unreadable case and grow its history without limit | five resolve rounds per case; after the first, only the tester's |
| the host's content-type header decided whether pinned bytes were read as HTML, so the same bytes could be read two ways | HTML is decided from the bytes alone; no header affects what the panel reads or what validators compare |
| honest validators seeing one outage as different failures disagreed, so nothing was recorded | validators compare readable or not, never the kind of failure |
| a bare `<` in a page ("ratio < 40 percent") swallowed the text after it; entities reached the panel undecoded; a JSON record's escapes were not read | one fixed rule for a page's text content; entities and JSON string escapes decoded; quotes checked against the same text |
| a document could crash a round (an absurdly long character reference) or slow it (thousands of comments) | decoding is fail-soft and parsing is one linear pass |
| a verdict could rest on a document cut off at the reading cap | a partly read item carries no positive verdict; the cap is 20,000 characters and documented |
| text addressed to the panel passed the scan through encodings: soft hyphens, fullwidth and lookalike letters, entities, JSON escapes and line breaks, invisible tag characters; and text in the panel's own answer format was not a marker | all decoded or folded before the scan; phrases match on word boundaries; the answer format is a marker |
| the scan then flagged ordinary lending text ("return policy violation", "a note to the assessor") | markers name only the adjudicator and this contract's own verdict words, and are published in `get_config` |
| an inconclusive verdict served criteria no validator compared | uncompared criteria are served as `null` |
| a stored quote could add or drop a sign or a comparison, or clip a number at its edge | signs, comparisons, decimal points and thousands separators are part of the words a quote must match |
| a lone surrogate in a label, a quote or a content type made views unreadable | refused in every stored string |
| the privacy guard skipped prohibited factors, evidence URLs, notes and quotes; and refused dated references | all screened; quotes of public evidence are screened for identifiers only |

Looked at and kept:

- **A confirmed violation still compares every criterion**, not only the ones its
  verdict rests on. The criteria are what a consumer reads, so they carry
  consensus, at the price of a validator who reads a side criterion differently
  refusing the round.
- **The marker scan is a heuristic and is narrow on purpose.** A phrasing the
  list does not name is not caught by it; a document that genuinely addresses
  "the adjudicator" - some claims-handling procedures do - stops rounds. The
  prompt frames every document as data, and every validator reads for itself.
- **The panel reads the text content of the pinned bytes by one fixed rule; it
  is not a browser.** Text a stylesheet or a `hidden` attribute would hide is
  read, because it is in the bytes both parties can see. A page that does not
  begin as an HTML document is read as written, tags included.
- **A host that stays down through a whole window ends the case** as
  `EVIDENCE_UNAVAILABLE`, on the record; the tester may file again while the
  challenge is open.

## Deliberately left out

- **Any financial action.** No approvals, denials, limits, freezes or transfers.
- **Personal data.** Synthetic references only; a guard refuses obvious
  identifiers in free text.
- **Accuracy or fairness metrics across many decisions.** One decision, one
  declared policy.
- **A frontend.** The contract is the product.
