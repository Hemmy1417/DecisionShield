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
| publisher (operator, auditor, governance body) | publish a challenge; cancel it before any case; contest a verdict once | change a published challenge or its policy; cancel once a case exists; spend the tester's contest; influence a reading |
| tester (red team, model risk, an advocate) | file one case per challenge; withdraw inside the resolve window; retry a round that could not read the evidence; contest once | file twice, cite a host the challenge did not name, declare an item without pinning it, change evidence after filing |
| keeper (anyone) | ask for the first resolve round; finalise; lapse | change any outcome; spend the tester's retries |
| validators | reproduce the round and refuse the leader | write a verdict; code derives it |
| a malicious leader | propose a forged payload | get it stored: every validator re-fetches, re-reads and re-derives |
| a malicious validator minority | vote against an honest leader | outvote an honest majority |
| an evidence host | be down, or serve other bytes | change what the panel reads from the pinned bytes; choose which of a case's items are read; pass a digest check with other bytes |
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

**Unbound evidence.** Every item a case declares is pinned to the sha256 of its
bytes; an unpinned item is refused at filing, whatever role it is given. The
digests are checked on every retrieval, in every round, and a contest cannot
bring better evidence.

**A host choosing what is read.** Three ways a host could shape a reading
without changing a pinned byte are closed. It cannot take down one record and
leave the rest to decide: any declared item that cannot be read makes the round
unavailable. It cannot change how bytes are parsed: HTML is decided from the
bytes, and no header affects the panel's text. And it cannot split honest
validators by failing differently for each: they compare readable or not.

**Burying a case with an outage.** The publisher usually hosts the policy, and
often the decision records. A resolve round during an outage records
`EVIDENCE_UNAVAILABLE` and the case stays `PENDING`; the retries are the
tester's alone. A contest round during an outage is recorded but neither
replaces the standing verdict nor spends anyone's contest, and it restarts the
window. If the evidence stays unreadable through the whole resolve window, the
case becomes final as `EVIDENCE_UNAVAILABLE` - the outage stays on the record -
and the tester may file again while the challenge is open.

**Spending the other party's contest.** Each party has its own; a party
contesting a verdict in its own favour uses only its own.

**Prompt injection aimed at the adjudicator.** Every document is scanned in code -
visible text, markup and attributes, title - with entities and JSON escapes
decoded up to three layers deep, hidden, combining and tag characters removed or
read, and fullwidth, mathematical, small-capital and Cyrillic, Greek or Armenian
lookalike letters folded to Latin. A marker phrase, or text in the panel's own
answer format, stops the round as `SOURCE_ADDRESSES_ADJUDICATOR`. Every
free-text field of the challenge and the case is scanned the same way at write
time, and a model's note that carries such text is dropped. The phrases are
published in `get_config`. The scan is a heuristic and is narrow on purpose: a
phrasing the list does not name is not caught, and a document that genuinely
addresses "the adjudicator" stops rounds. The second line is the prompt, which
frames every document as data; the third is that every validator reads for
itself.

**Injection aimed at the financial AI** is the subject of an adversarial-input
case, not an attack on this panel, and stays adjudicable.

**Stopping a case at the consistency check.** Contradictory evidence ends a round
as inconclusive before the violation is read, so that reading is the cheapest
place to bury one. It may not quote the explanation, it must quote two different
items, and the panel is told that a decision which does not follow from the
inputs is a violation question, not a contradiction.

**Altered quotes.** A stored quote must match the item's words in order, and a
minus sign, a comparison, a percent or currency sign, a decimal point and a
thousands separator count as part of those words, so a quote cannot change what
a number says or clip it at its edge. Grounding proves where a passage came
from, not that it is the best passage: two words still ground a reading, the
choice of passage is the leader's, and each validator re-derives the verdict
from its own reading.

**Malformed and hostile documents.** URLs are admitted only as `https` on port
443, to a DNS name inside the challenge's evidence domains, with no credentials,
fragments, encoded separators or dot-segments; that is admission hygiene, not
SSRF protection - the validators' runtime egress controls remain the real
boundary. At most 200,000 bytes of an item are fetched and 20,000 characters
read; a longer item is `PARTIAL` and carries no positive verdict. Parsing is one
linear pass and decoding never raises, so a document cannot crash or stall a
round. Two items may not declare the same bytes.

**A stale policy.** A case commits to the challenge hash, the policy version and
the policy document's sha256; any mismatch is refused at filing.

**Storage growth.** A case has at most five resolve rounds and three contest
rounds per party; listings are paginated.

**Fabricated or spliced support**, **malformed model output**, **replay** (one
case per tester per challenge), **expired challenges**, **double resolution** and
**unauthorised mutation** are each refused in code;
`tests/direct/test_ds_adversarial.py` works through them one at a time.

## Privacy and data minimisation

- Cases use **synthetic references**. No raw personal financial record is required
  or wanted on chain; evidence is referenced by URL and sha256, and the
  demonstration data is synthetic and marked so in every document.
- Every field a party **writes** - free text, labels, challenge text, prohibited
  factors - passes a **privacy guard** that refuses an email address, nine or more
  digits in a row, or digits grouped like a phone, card or social-security
  number. A dated reference such as `APP-2026-000123` passes. An evidence URL may
  not carry an email address.
- A **quote** is a passage of public, pinned evidence, and ordinary records carry
  timestamps and amounts, so a quote is refused only for an email address, a
  card-length run of digits, or a dashed identifier; such a quote is not stored.
  A model's note that carries an identifier is dropped.
- The guard is a heuristic that catches the obvious mistakes, not a privacy
  guarantee: a name, an address, an IBAN or an eight-digit account number would
  pass it, and a bare nine-digit amount is refused (write it with separators).
- No secret, credential, key or customer record is stored in the repository;
  signing keys live in a gitignored `.data/` directory and are never printed.

## Fail-closed policy

Both positive outcomes are guarded the same way: a confirmed violation and a
compliance finding each need every declared item read whole and matching its
pinned bytes, and the readings they rest on quoted from non-explanation
evidence; every other branch is `INCONCLUSIVE` or `EVIDENCE_UNAVAILABLE`. A rule
followed with a contradicted explanation is `CRITERIA_CONFLICT`, not compliance:
a system that gives a false reason for a lawful decision does not get a
compliance stamp. Compliance also needs evidence that a prohibited factor was
not used; a record that is silent about it reads `CRITERIA_UNCLEAR`.

## Limitations

- One decision, one declared policy: no statement about accuracy or fairness
  across many decisions.
- The readings are model judgements; where honest models split, nothing is stored.
- Public-source evidence is only as strong as the hosts a challenge names. A
  host that stays down through the whole resolve window ends the case as
  `EVIDENCE_UNAVAILABLE`; the tester can file again only while the challenge is
  open. A party who controls a host can delay finality by a bounded number of
  contest windows.
- The marker scan and the privacy guard are heuristics, in both directions: an
  unlisted phrasing passes, and a document that addresses "the adjudicator" for
  its own reasons stops rounds.
- The panel reads the text content of the pinned bytes by a fixed rule, not as a
  browser renders them: text hidden by a stylesheet or a `hidden` attribute is
  read, and a document that does not begin as HTML is read as written.
- An item longer than 20,000 characters cannot carry a positive verdict.
- Roles are the tester's labels: a tester could file the system's explanation as
  corroboration. The publisher's contest is the answer to a mislabelled case.
- One read contest per party.
- Identity is a wallet; the per-wallet cap bounds abuse, it does not prevent it.
- A StudioNet deployment reviewed adversarially by its author's tooling, not an
  independent production audit.

