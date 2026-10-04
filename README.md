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

| | |
|---|---|
| Network | GenLayer StudioNet, chain id 61999 |
| Contract | [`0x2Eeb9e62Cf44654a90cB7263eD4620b0bb3422E3`](https://explorer-studio.genlayer.com/address/0x2Eeb9e62Cf44654a90cB7263eD4620b0bb3422E3) |
| Explorer | `https://explorer-studio.genlayer.com/address/0x2Eeb9e62Cf44654a90cB7263eD4620b0bb3422E3` |
| Deployment tx | [`0x5d61744aee027560d56c42f5d0716aa225b29b35f5f15d962db2caff44fdfc48`](https://explorer-studio.genlayer.com/tx/0x5d61744aee027560d56c42f5d0716aa225b29b35f5f15d962db2caff44fdfc48) |
| Finality / status | FINALIZED, leader execution SUCCESS |
| Consensus result | AGREE x3, 2 validators idle |
| Deployment source commit | `913ccdb` |
| Current source parity | deployed source read back with `gen_getContractCode`: **byte-identical** to `contracts/decisionshield.py` on `main` |

Version 0.4.1. It supersedes four earlier deployments (`deploy/superseded/`) - see
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md#how-the-live-evidence-was-reached).
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

## Why GenLayer

| Without GenLayer | What you get |
|---|---|
| the operator's own compliance service | the party under test grades itself |
| one external reviewer or one model call | one trusted reporter whose reading nobody can check |
| a deterministic parser | cannot read a prose policy against a model's explanation |
| a price or data oracle | wrong problem: there is no number to report, only a reading |

## Delete GenLayer: what breaks?

The question is a reading of a prose policy against case evidence and a model's
account of itself. Delete GenLayer and that reading comes from one party, in
private. With it, several independent validators each fetch the same pinned
bytes, perform the reading themselves, refuse a leader whose verdict is
well-formed but wrong, and leave a typed record a third system can act on.
Deterministic code has no input from which to derive "the violation condition is
met" - consensus supplies it, and nothing else.

## Why this is not a rejected pattern

| Pattern | Why DecisionShield is not it |
|---|---|
| thin LLM wrapper | the model never chooses the verdict: it returns per-subject readings, and code derives the verdict, severity and compliance flag |
| generic AI app | one bounded question, typed outcomes, no UI, no chat |
| format-only validator | each validator re-fetches, re-reads, re-grounds every quote in its own bytes and re-derives the verdict |
| caller-authored evidence | the policy and every item a case declares are pinned to a sha256 the round re-checks, an unpinned item is refused, and the explanation is never evidence |
| toy storage | versioned challenges, bounded histories, a lifecycle with contest, finality and lapse |
| full application | contract only, no frontend, no funds |

## Evidence roles - and the explanation

| Role | What it is |
|---|---|
| `POLICY` | the challenge's policy document, re-fetched every round against its declared sha256 |
| `CASE_INPUT` | what the AI decided on - synthetic or redacted |
| `MODEL_OUTPUT` | what it decided, as the system recorded it |
| `EXPLANATION` | the system's own account of why |
| `CORROBORATION` | an external record to check the case against |

**Every item is pinned to the sha256 of its bytes**, and every item a case
declares must be readable for a round to be read at all: a host cannot change a
document, or choose which of its records the panel sees.

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
violation, and **both** positive verdicts need every declared item read whole
and matching its pinned bytes, with their deciding passages quoted from
non-explanation evidence.

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
               │ ▲  │ │                └─ contest: one read contest per party;
               │ └──┘ │                   every contest round restarts the window
               │  resolve with evidence unavailable: recorded, stays PENDING
               │  (five resolve rounds at most; after the first, the tester's)
               │      └─ withdraw_case (tester, inside the window) ──► CANCELLED
               └─ lapse_case (anyone, after the resolve window)
                    ├─ never read           ──► CANCELLED
                    └─ evidence unavailable ──► FINAL, EVIDENCE_UNAVAILABLE
```

An outage never ends a case early and never replaces a reading: a round that
cannot read the evidence is recorded and the case stays open, and a contest
round during an outage changes nothing and spends nothing. Each party has its
own contest, so neither can use up the other's.

| Step | Who |
|---|---|
| publish / cancel a challenge | the publisher - an operator's model-risk team, an auditor, a governance body |
| submit / withdraw a case | the tester - a red team, model risk, an advocate |
| resolve | anyone for the first round; the tester for a retry after a round that could not read the evidence |
| finalize, lapse | anyone; the state decides, not the caller |
| contest | the tester and the publisher, one read contest each |

## Contract surface

24 methods: 8 writes, 16 views, none payable. The views the brief names are all
there: `get_challenge`, `get_submission`, `get_verdict`,
`is_policy_violation_confirmed`, `get_policy_hash`, `get_evidence_status`,
`get_challenge_status`, `get_policy_version` - plus `get_resolution`,
`get_latest_resolution`, `get_history`, `get_actions`, `list_challenges`,
`list_submissions`, `get_stats` and `get_config`.

## Nondeterministic operations

| Call | Where | Why irreducibly nondeterministic |
|---|---|---|
| `gl.nondet.web.get` | `_fetch_source`, for the policy and each declared item | the documents live off chain; each validator must fetch them itself |
| `gl.nondet.exec_prompt` | `_node_round`, once per round | reading a prose policy against a case and an explanation is a judgement no parser makes |

## Deterministic responsibilities

Identity and authorisation; challenge and policy hashes and versions; URL and
host admission; pinning of every evidence item; the privacy guard; one case per
tester per challenge and ten open cases per tester; deadlines and windows from
transaction time; digest checks on every retrieval; how the pinned bytes become
the text the panel reads; the marker scan for text addressed to the adjudicator;
the code reasons that decide a round without the panel; quote grounding and the
which-item-may-be-quoted rule; the derivation of verdict, reason, severity,
criteria and evidence status; resolve retries, each party's contest, finality,
lapse and withdrawal, with caps on every round; bounded storage and pagination.

## Equivalence / validator design

Each validator reproduces the round from its own retrieval and model call, gates
the leader's payload against its own text, then compares what was retrieved and
what it leads to: what each node could do with each item and the digest of its
bytes, the verdict, the reason, and - for a positive verdict - every criterion.
Notes, quote choice and HTTP details may differ, and every record says so.
[`docs/CONSENSUS.md`](docs/CONSENSUS.md).

## Safety and failure semantics

Every ambiguity fails closed. A failed fetch, a digest that does not match, an
unreadable policy or any declared item that cannot be read is
`EVIDENCE_UNAVAILABLE`: recorded, never a verdict, and never the end of a case
while its window is open. Text addressed to the adjudicator, an unusable model
answer, contradictory or unclear evidence, a decision the record does not show,
an unclear reading, or a document read only in part is `INCONCLUSIVE`. Neither
is ever collapsed into compliance or violation, and where validators disagree
the round stores nothing. [`docs/CONSENSUS.md`](docs/CONSENSUS.md#failure-semantics).

## Financial safety, privacy, and no false guarantees

- Not a substitute for regulated decision-making, compliance review, model-risk
  management or professional oversight; no legal or regulatory certification.
- A compliant verdict does not prove a model safe; a confirmed violation does not
  prove intent; a case without one does not prove no other exists.
- Synthetic references only. Every field a party writes passes a privacy guard
  that refuses email addresses, long digit runs and digits grouped like a phone,
  card or social-security number - a heuristic, documented as such. No raw
  personal financial data is required or stored.

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

## Limitations

- Not legal, regulatory or financial advice, and not a certification.
- A verdict is about one decision against one declared policy, on the evidence
  evaluated - not proof of absolute truth about the model.
- Honest-majority assumption over validators; where honest models split, no
  majority forms and nothing is stored.
- Evidence availability depends on the hosts a challenge names. An outage is
  recorded, never a verdict; a host that stays down through a whole window ends
  the case as `EVIDENCE_UNAVAILABLE`, and a party who controls a host can delay
  finality by a bounded number of contest windows.
- Readings are model judgements: notes and quote choice vary between validators,
  and only the fields listed under validator design are compared.
- The marker scan and the privacy guard are heuristics, in both directions: no
  perfect prompt-injection or privacy guarantee, and a document that genuinely
  addresses "the adjudicator" stops rounds.
- The panel reads the text content of the pinned bytes by one fixed rule, not as
  a browser renders them, and at most 20,000 characters of an item; a longer item
  cannot carry a positive verdict.
- URL admission is hygiene, not SSRF protection: the validators' runtime egress
  controls are the real boundary.
- Histories, rounds and pages are bounded; one read contest per party.
- A StudioNet deployment reviewed adversarially four times by its author's own
  tooling - not an independent production audit.

## Verification

<!-- VERIFIED:START -->
| Check | Result |
|---|---|
| `python -m pytest tests/direct -q` | 184 passed |
| pickling of the nondeterministic closures | checked (`direct_vm.check_pickling = True`) |
| `genvm-lint check contracts/decisionshield.py --json` (`GENVM_VERSION=v0.3.0-rc7`) | lint ok (3 checks), validation ok, 24 methods (16 view, 8 write), exit 0 |
| `ruff check .` | clean |
| `python scripts/generate_fixtures.py --check` | 16 fixture files regenerate byte for byte |
| `python scripts/mutation_check.py` | 166 mutations, **166 killed, 0 survived** |
| adversarial review | four read-only rounds; the fourth found nothing on the verdict path or the lifecycle |
| `python scripts/deploy_studionet.py --verify` | deployed and repository sha256 equal, 24 schema methods |
| `python -m pytest tests/integration -q` | 9 passed, 1 skipped (the live-write test runs only with `DS_LIVE_WRITES=1`) |
| live run of record | 38 transactions, **15 of 15 outcomes held, 12 of 12 refusals refused, each for the reason it was sent to test** |

Every verdict the contract stores was reached on chain against the canonical
deployment: a confirmed violation, upheld by the publisher's contest; compliance;
a violation won by an applicant's injected note; four distinct inconclusive
reasons; two unavailable-evidence rounds that left their cases pending, one of
which stayed unreadable through its window, became final as unavailable and was
filed again by the same tester; two finalized verdicts read back through
`is_policy_violation_confirmed`; a lapse; and 12 refusals. Every transaction is
linked in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md#live-run-of-record).

The contract was read by an adversary four times, and changed each time until a
round found no way to a wrong verdict: see
[What the adversarial review changed](DECISION.md#what-the-adversarial-review-changed).
<!-- VERIFIED:END -->

## Reviewer fast path

```bash
git clone https://github.com/Hemmy1417/DecisionShield.git && cd DecisionShield
pip install -r requirements-test.txt
python scripts/fetch_genvm_bundle.py
python -m pytest tests/direct -q
python scripts/mutation_check.py
python scripts/deploy_studionet.py --verify
python -m pytest tests/integration -q
```

Then read:

1. [`DECISION.md`](DECISION.md) - the specification, written before the contract,
   and what the diagnostic passes and four adversarial reviews changed.
2. [`docs/CONSENSUS.md`](docs/CONSENSUS.md) - which evidence each reading may
   quote, and what validators compare.
3. `contracts/decisionshield.py` - `_verdict_for`, `_quotable`, `_code_reason`,
   `_privacy_error`.
4. [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) - every transaction of the run of
   record, and the seven passes before it.
5. `tests/direct/test_ds_adversarial.py` - the brief's adversarial matrix, one
   test at a time; `tests/direct/test_ds_review.py` and the three files after it -
   what each review found.

## Licence

MIT. See [`LICENSE`](LICENSE).
