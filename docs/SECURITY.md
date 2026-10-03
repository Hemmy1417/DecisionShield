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
| a malicious leader | propose a forged payload | get it stored: every validator re-fetches, re-reads and re-derives |
| a malicious validator minority | vote against an honest leader | outvote an honest majority |
| a malicious evidence host or web page | serve different bytes, or text addressed to the panel | pass a pinned digest check; stop being caught by the marker scan for the visible, hidden and markup forms it covers |
| a downstream consumer | read any view | change anything; it acts in its own process |

## Trust assumptions

- An honest majority of validators, running independent model calls.
- The hosts a challenge names serve the bytes the case pinned; if they do not,
  the case is `EVIDENCE_UNAVAILABLE`, not a verdict.
- The publisher's policy says what the publisher means: DecisionShield judges
  against the policy as written and hashed, not as intended.
- Transaction time (`gl.message_raw["datetime"]`) is the clock for deadlines
  and windows.
- The model panel can read English prose policies and structured case records;
  where honest models split, nothing is stored.

## Input attacks

**The AI's explanation as evidence.** An explanation is the system's claim about
its own decision. A finding a verdict rests on can never be quoted from an
`EXPLANATION` item, and the decision itself is read only from the model's
recorded output.

**Prompt injection aimed at the adjudicator.** Every document is scanned in code -
visible text, markup and attributes, title - with hidden characters, soft hyphens,
the zero-width joiner, numeric and word-splitting named entities, JSON escapes
and tag or comment splits undone, and fullwidth forms and Cyrillic or Greek
lookalike letters folded to Latin. Text addressed to the adjudicator stops the
round as `SOURCE_ADDRESSES_ADJUDICATOR`. Every free-text field of the challenge
and the case is scanned in the same decoded form at write time, and a model's
note that carries such text is dropped. The list is narrow and the scan is a
heuristic: text written in the panel's own answer format, or a phrasing the list
does not name, is not caught by it. The second line is the prompt, which frames
every document as data, and the third is that every validator reads for itself.

**Injection aimed at the financial AI** is the subject of an adversarial-input
case, not an attack on this panel. The marker list is narrow on purpose, so such
a case is adjudicated rather than silenced.

**Swapping a document.** The policy's sha256 is fixed in the challenge and each
pinned item's at filing; both are checked on every retrieval, in every round.
Different bytes are `EVIDENCE_DIGEST_MISMATCH`, and a contest cannot bring better
evidence.

**A stale policy.** A case commits to the challenge hash, the policy version and
the policy document's sha256; any mismatch is refused at filing.

**Unbound evidence.** A `LIVE` item has no digest. Neither positive verdict is
reached unless every readable item that can be evidence is pinned; only the
explanation may be `LIVE`. This is decided from the case, so a reading that
quotes only the policy cannot carry a verdict that rests on unbound inputs.

**Burying a case with an outage.** The publisher usually hosts the policy. If it
takes that host down, a resolve round records `EVIDENCE_UNAVAILABLE` and the case
stays `PENDING`, open to be resolved again once the host is back; a contest round
during an outage is recorded but neither replaces the standing verdict nor
spends the contest. If the evidence stays unreadable through the whole window,
the case becomes final as `EVIDENCE_UNAVAILABLE` - the outage stays on the record
- and the tester may file again while the challenge is open.

**Altered quotes.** A stored quote must match the item's words in order, and a
minus sign, a comparison, a percent sign or a decimal point counts as a word, so
a quote cannot change what a number says. Grounding proves where a passage came
from, not that it is the best passage: two words still ground a reading, and each
validator re-derives the verdict from its own reading.

**Fabricated or spliced support**, **malformed model output**, **replay** (one case
per tester per challenge, enforced on `challenge_id + tester`), **expired
challenges**, **double resolution** and **unauthorised mutation** are each refused
in code; `tests/direct/test_ds_adversarial.py` works through them one at a time.

## Privacy and data minimisation

- Cases use **synthetic references**. No raw personal financial record is required
  or wanted on chain; evidence is referenced by URL and sha256, and the
  demonstration data is synthetic and marked so in every document.
- Every free-text field - and every label, challenge text field and prohibited
  factor - passes a **privacy guard** that refuses an email address or a run of
  nine or more digits (dashes allowed, so a phone number in the usual form is
  caught). An evidence URL may not carry an email address, and a model's note
  that carries an identifier is dropped rather than stored. It is a
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
- One contest per case, for whichever party uses it first; an unavailable
  contest round does not spend it.
- A host that stays down through the whole resolve window ends the case as
  `EVIDENCE_UNAVAILABLE`; the tester can file again only while the challenge is
  open.
- Identity is a wallet; the per-wallet cap bounds abuse, it does not prevent it.
