# Deployment

The canonical StudioNet deployment, how to reproduce it, the diagnostic passes
that shaped it, and the live run of record. Every value below is read from
`deploy/deployment.json` and `deploy/live_run_transcript.json`.

## Environment

| | |
|---|---|
| Network | GenLayer StudioNet, chain id 61999, `https://studio.genlayer.com/api` |
| Explorer | `https://explorer-studio.genlayer.com` |
| Wallets | the deployer key in `.data/deployer.json`; the demo wallets' keys in `.data/demo_wallets.json` (`scripts/make_wallets.py`), public addresses in `fixtures/wallets.json`; `.data/` is gitignored and no key is ever printed |
| Toolchain | Python 3.12, genlayer-test 0.29.2, genlayer-py 0.16.3, genvm-linter 0.11.0 with GenVM bundle v0.3.0-rc7 |
| Runner | `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` |

The linter picks the newest GenVM bundle in its cache; pin the one the suite was
verified against:

```bash
GENVM_VERSION=v0.3.0-rc7 genvm-lint check contracts/decisionshield.py --json
```

## Reproduce

```bash
pip install -r requirements-test.txt
python scripts/fetch_genvm_bundle.py
python -m pytest tests/direct -q
python scripts/deploy_studionet.py
python scripts/deploy_studionet.py --verify
python scripts/make_wallets.py
python scripts/live_run.py <address> --raw-base https://raw.githubusercontent.com/<owner>/<repo>/<commit>/fixtures/ --phase full
python -m pytest tests/integration -q
```

## Canonical deployment

| | |
|---|---|
| Date | 2026-10-03 09:52:07Z |
| Deployment method | `scripts/deploy_studionet.py` - genlayer-py 0.16.3 against the StudioNet RPC, then `gen_getContractCode` and `gen_getContractSchema` read back (GenLayer CLI 0.39.2 is installed but was not the deployment route) |
| Deployer public address | `0xE5A637385057B868D4B464605D3d65d855bab0B6` (a fresh dedicated signer; key in the gitignored `.data/deployer.json`) |
| Contract | [`0x2Eeb9e62Cf44654a90cB7263eD4620b0bb3422E3`](https://explorer-studio.genlayer.com/address/0x2Eeb9e62Cf44654a90cB7263eD4620b0bb3422E3) |
| Deployment transaction | [`0x5d61744aee027560d56c42f5d0716aa225b29b35f5f15d962db2caff44fdfc48`](https://explorer-studio.genlayer.com/tx/0x5d61744aee027560d56c42f5d0716aa225b29b35f5f15d962db2caff44fdfc48) |
| Status | FINALIZED, leader execution SUCCESS, votes AGREE x3 (two validators idle) |
| Source commit | `913ccdb4a73ada4979fdc5a8b329e898d151a29c` |
| Contract blob | `bcb998937b52feebef461129dff1d97e8713edfe` |
| Source | byte-identical to the repository (sha256 `d7cb4e43...1377`, in `deploy/deployment.json`) |
| Schema | 24 methods (16 view, 8 write), read from the chain |

## Verification of record

| Check | Result |
|---|---|
| Source parity | deployed source read back with `gen_getContractCode`; sha256 equal to `contracts/decisionshield.py` on `main` (`python scripts/deploy_studionet.py --verify`) |
| Integration suite | `python -m pytest tests/integration -q`: 9 passed, 1 skipped (the live-write test runs only with `DS_LIVE_WRITES=1`); each test also passes run alone |
| Disposable deployments | none were used as evidence. The four earlier deployments, `0x99612D2D`, `0xc95E80E2`, `0x6B3C122f` and `0x8E2c6627`, are superseded and recorded under `deploy/superseded/`; none is the canonical deployment |

## How the live evidence was reached

Seven passes ran before the run of record, six of them on four earlier
deployments. Four changed the contract, one changed a fixture and one changed
the run script. All are kept under `deploy/diagnostics/`.

| Pass | Deployment | What it found | What changed |
|---|---|---|---|
| `pass1_superseded_0x99612d2d` | first, `0x99612D2D` | the clearest violating case (DS01) read `INCONCLUSIVE` / `EVIDENCE_CONTRADICTORY`, and the publisher's contest repeated it: the panel counted the system's own false explanation - a ratio problem the inputs do not show - as evidence contradicting the inputs. The pass was stopped there | **the contract**: an explanation is a claim, not evidence, so contradictory evidence may no longer be quoted from it and the consistency subject is asked about the evidence items only; redeployed |
| `pass2_0xc95e80e2` | second, `0xc95E80E2` | 37 transactions, 14 of 14 outcomes held, 11 of 11 refused | nothing |
| `pass3_record_v1_0xc95e80e2` | second | the first run of record: 37 transactions, 14 of 14 held, 11 of 11 refused. A read-only adversarial review of the contract afterwards found real defects no test, sweep or live outcome had shown - above all, that the operator under test could bury a case by taking its own policy host down, and that a positive verdict could rest on a `LIVE` input if the readings quoted only the policy | **the contract** (v0.2.0): see [What the adversarial review changed](../DECISION.md#what-the-adversarial-review-changed); redeployed, and this run demoted to a diagnostic |
| `pass4_0x6b3c122f` | third, `0x6B3C122f` | 39 transactions, 14 of 16 outcomes held, 11 of 11 refused. The compliant case (DS02) read `INCONCLUSIVE` / `CRITERIA_UNCLEAR`: the leader's model would not rule out that age was used, because the inputs carry an age band and the decision record named only its top factor. Three validators agreed, two disagreed | the fixture: the decision record now lists its factor weights, with age at 0.00. The panel was right to hesitate |
| `pass5_0x6b3c122f` | third | stopped after two cases. The violating case (DS01) was confirmed, then the publisher's contest read it `INCONCLUSIVE` / `EVIDENCE_CONTRADICTORY` and three of five validators agreed: the second panel called the inputs (which qualify for approval) and the output (a decline driven by age) "contradictory". That is not two records disagreeing about a fact - it is the violation | **the contract** (v0.2.1): the consistency subject now says a wrong decision is not a contradiction, defines one as two items giving different values for the same fact, and code requires a contradiction to quote two different items; redeployed |
| `pass6_record_v2_0x8e2c6627` | fourth, `0x8E2c6627` | the second run of record: 39 transactions, 16 of 16 outcomes held, 11 of 11 refused, no validator disagreeing. Three more read-only reviews followed, each after the previous round's fixes. The second and third found real defects again - a host could take down one pinned record and leave the rest to decide the case; an unpinned input labelled an "explanation" could carry a verdict; a header decided how pinned bytes were read; the favoured party could spend the only contest. The fourth found nothing on the verdict path | **the contract** (v0.3.0 to v0.4.1): see [What the adversarial review changed](../DECISION.md#what-the-adversarial-review-changed); redeployed, and this run demoted to a diagnostic |
| `pass7_0x2eeb9e62` | canonical | 38 transactions, 15 of 15 outcomes held, 12 of 12 refused - but one refusal was for the wrong reason: the case sent to test the evidence-domain rule was refused for declaring an unpinned item, which v0.4.0 now checks first. The script counted any refusal as held | the run script: the test case is pinned, and a refusal now holds only if it is for the reason it was sent to test |

The lesson of the first row: the design already said an explanation is a claim
about a decision and never evidence for it, and enforced that for every finding
a verdict rests on - except the consistency check. A lying explanation is exactly
what a violating case looks like; counted as contradictory evidence, it would
make the cases DecisionShield exists to catch inconclusive.

The lesson of the fifth is the first again, one step on: any violation can be
described as "the inputs and the outcome do not fit together", and a question
about consistency that leaves room for that description lets a panel stop at the
check that comes before the one that matters. A contest is a second panel, so it
found the reading the first panel did not take.

The lesson of the fourth: a compliance verdict needs evidence that a prohibited
factor was *not* used, and a record that says nothing about it leaves a careful
reader unable to say so. That is the contract failing closed, as designed.

The lesson of the third and the sixth is one lesson: a green suite, a clean
sweep and a live run that holds every outcome show the contract does what its
author meant. They do not show that what the author meant is safe against the
parties it judges. That took a reader looking for a way to win - four times,
until a round found no way to a wrong verdict and no way for one party to
outlast the other.

## Live run of record

`python scripts/live_run.py` against the canonical deployment,
2026-10-04 01:53:41Z to 2026-10-04 02:54:34Z, the
policy served from `raw.githubusercontent.com` and the case evidence from the
jsDelivr mirror of the same commit, `82963e7`, from fourteen accounts: a
publisher, a keeper, a stranger and eleven testers, one per case.

**38 transactions, 15 of 15 outcomes held, 12 of 12 refusals refused, each for
the reason it was sent to test; no validator disagreed in any round.** Every
verdict the contract stores was reached on chain: a decline the policy forbade,
resting on the age band, `POLICY_VIOLATION_CONFIRMED` with severity `HIGH`, and
upheld by the publisher's contest; a lawful decline `POLICY_COMPLIANT`; an
approval an applicant's own note talked the model into, confirmed as a violation;
four distinct `INCONCLUSIVE` reasons; a wrong digest and an unpublished decision
record each recorded as `EVIDENCE_UNAVAILABLE` with the case left `PENDING`; the
second of those final as unavailable once its window passed, and filed again by
the same tester; two verdicts finalized and read back through
`is_policy_violation_confirmed`; a lapse; and 12 refusals, among them a case
that declared unpinned evidence.

One step was sent twice. The script sent `finalize` for the compliant case five
seconds before its contest window closed; the contract refused it ("the contest
window closes at ..."), which is the rule working, and the script's wait was
corrected. The step was sent again after the window and is the transaction in the
table; the refused attempt is in `deploy/live_run.out`.

| Scenario | Step | Transaction | Recorded | |
|---|---|---|---|---|
| lifecycle | `challenge:credit-line` | [`0x6131139b...`](https://explorer-studio.genlayer.com/tx/0x6131139b3ab5063f573fb703088b027ac5a02312f7210c5713e50a9b958a94c8) | publish_challenge FINALIZED/SUCCESS |  |
| lifecycle | `file:DS11` | [`0xfa746da0...`](https://explorer-studio.genlayer.com/tx/0xfa746da09a0d3b215d6495cc599af281a4e1ffb879db4501126e5cc6cb32d7e2) | submit_case FINALIZED/SUCCESS |  |
| lifecycle | `file:DS01` | [`0xc57ebb45...`](https://explorer-studio.genlayer.com/tx/0xc57ebb4510c0718c1fb89ed3452841bdfba9ab42d53dd3775321d6bb0aa111bc) | submit_case FINALIZED/SUCCESS |  |
| success | `resolve:DS01` | [`0x916aae0a...`](https://explorer-studio.genlayer.com/tx/0x916aae0ac6f787c1fd557639c060f934e5bfbe7cbc57e2377e5a136c04754e4b) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| lifecycle | `contest:DS01` | [`0x55796b77...`](https://explorer-studio.genlayer.com/tx/0x55796b77e05f1c1e2364fe67a7363fc1cb2b8a5a052c31d623d10f7fc41c68f0) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| lifecycle | `file:DS02` | [`0x6c39448f...`](https://explorer-studio.genlayer.com/tx/0x6c39448f962b61e01fe724e63305c102ee2ddda8b75046dc84535fc13458a7b0) | submit_case FINALIZED/SUCCESS |  |
| success | `resolve:DS02` | [`0xafc5620c...`](https://explorer-studio.genlayer.com/tx/0xafc5620c28f6e892d0153790efc5a0ca61e6691b9d738219188501922823fe9a) | POLICY_COMPLIANT / RULE_FOLLOWED | held |
| lifecycle | `file:DS03` | [`0x59cb29d6...`](https://explorer-studio.genlayer.com/tx/0x59cb29d6d19cf20e87e54eaa957898bd74bbaea3ee19a3232d6c4e59e3e2cc49) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS03` | [`0x6c222bba...`](https://explorer-studio.genlayer.com/tx/0x6c222bbaa02e3338fcd44b957087544e1280ab6854a47e531e46d10022a5a7a1) | INCONCLUSIVE / DECISION_NOT_RECORDED | held |
| lifecycle | `file:DS04` | [`0xb0fed237...`](https://explorer-studio.genlayer.com/tx/0xb0fed2378b6515864a52042fe58389f931c5e3db9b8684308831004316d32ac9) | submit_case FINALIZED/SUCCESS |  |
| success | `resolve:DS04` | [`0x66422db6...`](https://explorer-studio.genlayer.com/tx/0x66422db60f51ac35e350a737484474063d4f06832a41d80fcfdaa9d1c53bd461) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| lifecycle | `file:DS05` | [`0x3994b0d2...`](https://explorer-studio.genlayer.com/tx/0x3994b0d224a41f6e6fa742c859083cc1569aa1ae2af715657198e01f0a0d8f66) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS05` | [`0xe30bfc4a...`](https://explorer-studio.genlayer.com/tx/0xe30bfc4a3a39c99ed32e3b2f3ec96cee5391e343a14d67a52bf3df3e582e1935) | INCONCLUSIVE / CRITERIA_CONFLICT | held |
| lifecycle | `file:DS06` | [`0xbb7eb34a...`](https://explorer-studio.genlayer.com/tx/0xbb7eb34a6ff88050c487bbddd288056b528bad981b40ef6178521cc11e03fadb) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS06` | [`0xaa862d1b...`](https://explorer-studio.genlayer.com/tx/0xaa862d1bbbd77e7c8191826aaf44a00a69193ba8eaaf41d74ed3e08bd74d4474) | INCONCLUSIVE / EVIDENCE_CONTRADICTORY | held |
| lifecycle | `file:DS07` | [`0xf73c7176...`](https://explorer-studio.genlayer.com/tx/0xf73c71764c73fd9f984091e2e44d42bb8c055513df164c91ff2b5fcb23af7570) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS07` | [`0xd684054f...`](https://explorer-studio.genlayer.com/tx/0xd684054f4a4afacb5562b21116284e8e13ecc753dbb690acfcf6f6cb9e9655a0) | INCONCLUSIVE / SOURCE_ADDRESSES_ADJUDICATOR | held |
| lifecycle | `file:DS08` | [`0xa6647341...`](https://explorer-studio.genlayer.com/tx/0xa66473413584514c7eb5406149da1190eac5f716902fea5362e97e38ccb65db5) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS08` | [`0x7d766450...`](https://explorer-studio.genlayer.com/tx/0x7d7664504be86cc888d435dc26a6663ba2742ed6ffd2681051975e89abd256e3) | EVIDENCE_UNAVAILABLE / EVIDENCE_DIGEST_MISMATCH | held |
| lifecycle | `file:DS09` | [`0x01fc2d05...`](https://explorer-studio.genlayer.com/tx/0x01fc2d058efb78667b686ab7692ee508406c8cb1c3fd9a0348367d36cfa06d6b) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS09` | [`0xa0f16ef5...`](https://explorer-studio.genlayer.com/tx/0xa0f16ef550b6097ae583a8903c1e84acd13c2ee230abadb53043864050b61a94) | EVIDENCE_UNAVAILABLE / REQUIRED_EVIDENCE_UNREADABLE | held |
| success | `finalize:DS01` | [`0xd4284979...`](https://explorer-studio.genlayer.com/tx/0xd4284979258a90abbc38c3b2ef119a57b4268a81615d16c87199e1aa333a9a85) | FINAL; is_policy_violation_confirmed confirmed=true, final=true | held |
| success | `finalize:DS02` | [`0xa7bd02c0...`](https://explorer-studio.genlayer.com/tx/0xa7bd02c0fc582ceb2dc5589ad9d40f4a885a270be1ed8e78f61cf5fe9bd1b6cc) | FINAL; is_policy_violation_confirmed confirmed=false, final=true | held |
| lifecycle | `lapse:DS11` | [`0x9dcef1cf...`](https://explorer-studio.genlayer.com/tx/0x9dcef1cf6f153acc31e9352e7e4aeb20c139c2316448c9d1fed27f470708bc87) | CANCELLED / LAPSED | held |
| lifecycle | `lapse:DS09` | [`0x207a178d...`](https://explorer-studio.genlayer.com/tx/0x207a178df5b43f651141d7bc673c09dae4a0bc56c7202402c704588663154b4b) | FINAL; EVIDENCE_UNAVAILABLE / REQUIRED_EVIDENCE_UNREADABLE | held |
| lifecycle | `refile:DS09` | [`0x1d888649...`](https://explorer-studio.genlayer.com/tx/0x1d8886492c583846f7efe59e029baa1b62950c9dfe6915418d609043ceeb934b) | a new case from the same tester: DC-000022 | held |
| negative | `refuse:stale_policy_version` | [`0xf7096df1...`](https://explorer-studio.genlayer.com/tx/0xf7096df1a92cafd94218df6aa064725546d099fd2817f45110e546a74ec6d608) | refused: policy_version is not the version this challenge judges under: 2026-09 | held |
| negative | `refuse:policy_hash_mismatch` | [`0x35785540...`](https://explorer-studio.genlayer.com/tx/0x357855402f17deb3835151dadd4a93f29313054e37ba0b27885aea3d3d15b557) | refused: policy_sha256 does not match the challenge's policy document | held |
| negative | `refuse:personal_identifier` | [`0x12fe5177...`](https://explorer-studio.genlayer.com/tx/0x12fe5177974889684ca877cd33f0ce1b1145a36bac97752475b4c9c5300d6907) | refused: subject_reference must not contain a long digit sequence (an account or ID number): use a synthetic reference | held |
| negative | `refuse:email_in_summary` | [`0x25dc9a1d...`](https://explorer-studio.genlayer.com/tx/0x25dc9a1dbbfa08de3351021fc6330ff397538634b03eb590242a8c2bd6d796a1) | refused: input_summary must not contain an email address: use a synthetic reference | held |
| negative | `refuse:outside_domains` | [`0x16cee546...`](https://explorer-studio.genlayer.com/tx/0x16cee54635ee2b2ad33733d7e2cc32d93fabb65eb8cfd7fbad053e055aa24ba9) | refused: evidence[0] host is outside the challenge's evidence domains | held |
| negative | `refuse:explanation_addresses_adjudicator` | [`0xf205d405...`](https://explorer-studio.genlayer.com/tx/0xf205d4057bcd52c21d9db16edf978db0f7f2fa24432e1659ed77dbf173485000) | refused: decision_explanation must not contain instructions to the evaluator or hidden text | held |
| negative | `refuse:unpinned_evidence` | [`0x0ad939a2...`](https://explorer-studio.genlayer.com/tx/0x0ad939a2a0bc913c4626e4186775ff91813b613d65c07213be5fbcf62a8154d9) | refused: evidence[0] kind must be one of: PINNED | held |
| negative | `refuse:second_case_same_tester` | [`0x32e3998c...`](https://explorer-studio.genlayer.com/tx/0x32e3998c62b8ff837af86622e845d8de5eba4148a0e20e0be48fc844f679a067) | refused: this account already filed DC-000015 against this challenge | held |
| negative | `refuse:cancel_with_cases` | [`0x36e7bf4c...`](https://explorer-studio.genlayer.com/tx/0x36e7bf4cf6a0ad432c7e45686ceec11645c87ffc98d21612a72f156af337f518) | refused: this challenge already has cases and cannot be cancelled; it closes at its deadline | held |
| negative | `refuse:double_resolution` | [`0xbcb2838e...`](https://explorer-studio.genlayer.com/tx/0xbcb2838e64acb111287988fd9ce9598a396cc5a98c534a893e41d8d9618b8413) | refused: only a PENDING case is resolved | held |
| negative | `refuse:stranger_contest` | [`0xa46836ee...`](https://explorer-studio.genlayer.com/tx/0xa46836eedf86ad27911aaf6c28e9b836e4efd53fac00c7df7a14fd8b6c461156) | refused: only the tester or the challenge's publisher contests a verdict | held |
| negative | `refuse:stranger_withdraw` | [`0x8807d451...`](https://explorer-studio.genlayer.com/tx/0x8807d4518466528e47fbaf14ad35cb8e8d06bfb93ae1a7a6b69fef3ec31fa702) | refused: only the tester withdraws their own case | held |

## Mutation sweeps

| Sweep | Result |
|---|---|
| `deploy/mutation_sweep_first.txt` - the first sweep, on v0.1.0, before the tests it asked for | 85 mutations, 80 killed, 5 survived |
| `deploy/mutation_sweep_v1.txt` - v0.1.0 and its final suite | 85 mutations, 85 killed, 0 survived |
| `deploy/mutation_sweep_v2_first.txt` - the first sweep of v0.2.1 | 110 mutations, 109 killed, 1 survived |
| `deploy/mutation_sweep_v021.txt` - v0.2.1 and its final suite | 110 mutations, 110 killed, 0 survived |
| `deploy/mutation_sweep.txt` - the sweep of record, on the canonical v0.4.1 contract and the final suite | 166 mutations, **166 killed, 0 survived** |

Every survivor of the first sweep was a gap in the tests, and each now has the
test that kills it: a prohibited factor, and separately a contradicted
explanation, beside an unmet violation condition must not read as compliance
(both are `CRITERIA_CONFLICT`); an IP literal is refused as an evidence host; a
case cannot be filed against a cancelled challenge; and the record of a `LIVE`
item keeps only its status, never a digest or byte count that validators did not
compare. The mutations added since v0.1.0 each break one fix from an
adversarial review or a diagnostic pass, and each is killed by the test written
for that fix (`tests/direct/test_ds_review.py` and the three files after it). The
one survivor of the first v0.2.1 sweep was an older test the new two-item rule
had quietly disarmed: it quoted the explanation alone, which the new rule refuses
for a second reason, so the mutation it was written to catch no longer changed
its outcome. It now quotes the explanation beside a real item.
