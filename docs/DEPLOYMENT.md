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
| Date | 2026-10-03 04:22:26Z |
| Deployment method | `scripts/deploy_studionet.py` - genlayer-py 0.16.3 against the StudioNet RPC, then `gen_getContractCode` and `gen_getContractSchema` read back (GenLayer CLI 0.39.2 is installed but was not the deployment route) |
| Deployer public address | `0xE5A637385057B868D4B464605D3d65d855bab0B6` (a fresh dedicated signer; key in the gitignored `.data/deployer.json`) |
| Contract | [`0x8E2c66279fB5Fa0Ab6867573407aeA5787Baf467`](https://explorer-studio.genlayer.com/address/0x8E2c66279fB5Fa0Ab6867573407aeA5787Baf467) |
| Deployment transaction | [`0x131cdb62f0a0203c816d2b2d96616d2066101d4d08e23913faeda7480decc262`](https://explorer-studio.genlayer.com/tx/0x131cdb62f0a0203c816d2b2d96616d2066101d4d08e23913faeda7480decc262) |
| Status | FINALIZED, leader execution SUCCESS, votes AGREE x3 (two validators idle) |
| Source commit | `0fca5ad7f084c1859fefc1f4e62492df2209ac85` |
| Contract blob | `028876fb03226ec22cffab51c840078064b40925` |
| Source | byte-identical to the repository (sha256 `d99b97e4...5019`, in `deploy/deployment.json`) |
| Schema | 24 methods (16 view, 8 write), read from the chain |

## Verification of record

| Check | Result |
|---|---|
| Source parity | deployed source read back with `gen_getContractCode`; sha256 equal to `contracts/decisionshield.py` on `main` (`python scripts/deploy_studionet.py --verify`) |
| Integration suite | `python -m pytest tests/integration -q`: 9 passed, 1 skipped (the live-write test runs only with `DS_LIVE_WRITES=1`); each test also passes run alone |
| Disposable deployments | none were used as evidence. The three earlier deployments, `0x99612D2D`, `0xc95E80E2` and `0x6B3C122f`, are superseded and recorded under `deploy/superseded/`; none is the canonical deployment |

## How the live evidence was reached

Five passes ran before the run of record, on three earlier deployments. Three
changed the contract and one changed a fixture. All are kept under `deploy/diagnostics/`.

| Pass | Deployment | What it found | What changed |
|---|---|---|---|
| `pass1_superseded_0x99612d2d` | first, `0x99612D2D` | the clearest violating case (DS01) read `INCONCLUSIVE` / `EVIDENCE_CONTRADICTORY`, and the publisher's contest repeated it: the panel counted the system's own false explanation - a ratio problem the inputs do not show - as evidence contradicting the inputs. The pass was stopped there | **the contract**: an explanation is a claim, not evidence, so contradictory evidence may no longer be quoted from it and the consistency subject is asked about the evidence items only; redeployed |
| `pass2_0xc95e80e2` | second, `0xc95E80E2` | 37 transactions, 14 of 14 outcomes held, 11 of 11 refused | nothing |
| `pass3_record_v1_0xc95e80e2` | second | the first run of record: 37 transactions, 14 of 14 held, 11 of 11 refused. A read-only adversarial review of the contract afterwards found real defects no test, sweep or live outcome had shown - above all, that the operator under test could bury a case by taking its own policy host down, and that a positive verdict could rest on a `LIVE` input if the readings quoted only the policy | **the contract** (v0.2.0): see [What the adversarial review changed](../DECISION.md#what-the-adversarial-review-changed); redeployed, and this run demoted to a diagnostic |
| `pass4_0x6b3c122f` | third, `0x6B3C122f` | 39 transactions, 14 of 16 outcomes held, 11 of 11 refused. The compliant case (DS02) read `INCONCLUSIVE` / `CRITERIA_UNCLEAR`: the leader's model would not rule out that age was used, because the inputs carry an age band and the decision record named only its top factor. Three validators agreed, two disagreed | the fixture: the decision record now lists its factor weights, with age at 0.00. The panel was right to hesitate |
| `pass5_0x6b3c122f` | third | stopped after two cases. The violating case (DS01) was confirmed, then the publisher's contest read it `INCONCLUSIVE` / `EVIDENCE_CONTRADICTORY` and three of five validators agreed: the second panel called the inputs (which qualify for approval) and the output (a decline driven by age) "contradictory". That is not two records disagreeing about a fact - it is the violation | **the contract** (v0.2.1): the consistency subject now says a wrong decision is not a contradiction, defines one as two items giving different values for the same fact, and code requires a contradiction to quote two different items; redeployed |

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

The lesson of the third: a green suite, a clean sweep and a live run that holds
every outcome show the contract does what its author meant. They do not show
that what the author meant is safe against the parties it judges. That took a
reader looking for a way to win.

## Live run of record

`python scripts/live_run.py` against the canonical deployment,
2026-10-03 04:22:50Z to 2026-10-03 05:20:42Z, the
policy served from `raw.githubusercontent.com` and the case evidence from the
jsDelivr mirror of the same commit, `82963e7`, from fourteen accounts: a
publisher, a keeper, a stranger and eleven testers, one per case.

**39 transactions, 16 of 16 outcomes held, 11 of 11 refusals refused; no
validator disagreed in any round.** Every verdict the contract can store was
reached on chain: a decline the policy forbade, resting on the age band,
`POLICY_VIOLATION_CONFIRMED` with severity `HIGH`, and upheld by the publisher's
contest; a lawful decline `POLICY_COMPLIANT`; an approval an applicant's own note
talked the model into, confirmed as a violation; four distinct `INCONCLUSIVE`
reasons; a wrong digest and an unpublished decision record each recorded as
`EVIDENCE_UNAVAILABLE` with the case left `PENDING`; the second of those final as
unavailable once its window passed, and filed again by the same tester; two
verdicts finalized and read back through `is_policy_violation_confirmed`; a
lapse; and eleven refusals, each for the reason it was sent to test.

| Scenario | Step | Transaction | Recorded | |
|---|---|---|---|---|
| lifecycle | `challenge:credit-line` | [`0x06e5cfc6...`](https://explorer-studio.genlayer.com/tx/0x06e5cfc68748418e0378e12ec1f037c087f383a6719b9a890b37d369be715215) | publish_challenge FINALIZED/SUCCESS |  |
| lifecycle | `file:DS11` | [`0x678d51d4...`](https://explorer-studio.genlayer.com/tx/0x678d51d411af6b7da2c3274263b7254249bb98d5f7532b3f98293a079630fe76) | submit_case FINALIZED/SUCCESS |  |
| lifecycle | `file:DS01` | [`0x93de9b61...`](https://explorer-studio.genlayer.com/tx/0x93de9b61684789ec1e23d0c7bb9de31f3d905fb4d2d60e764f5b7ae06698c290) | submit_case FINALIZED/SUCCESS |  |
| success | `resolve:DS01` | [`0x57d03ca6...`](https://explorer-studio.genlayer.com/tx/0x57d03ca6af898b7bad9d70dce2af4c742303d1bfaed2c7bcb23a1abd57f15c95) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| lifecycle | `contest:DS01` | [`0xea8cffb1...`](https://explorer-studio.genlayer.com/tx/0xea8cffb113bb86ed96802ccef7a3c710ba143737bd39eaaa4a42e720c33c4659) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| lifecycle | `file:DS02` | [`0xbc924276...`](https://explorer-studio.genlayer.com/tx/0xbc9242763851897fac5c078d4521633aa9570333f036c695ccf590f8fe324f53) | submit_case FINALIZED/SUCCESS |  |
| success | `resolve:DS02` | [`0xa8f6ca41...`](https://explorer-studio.genlayer.com/tx/0xa8f6ca4125b6cf3ff68170175b1c1d3cee7c345e4634aa0c9bce51eb895c159c) | POLICY_COMPLIANT / RULE_FOLLOWED | held |
| lifecycle | `file:DS03` | [`0xe7278695...`](https://explorer-studio.genlayer.com/tx/0xe7278695f0cc6ea6c25d063bac360716c377adaf3f542e817c0f0dff78f4f2e1) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS03` | [`0xc2995c6e...`](https://explorer-studio.genlayer.com/tx/0xc2995c6ef5d30ec91ce398268b8d20a1d19123feb6a0c0212e00f0cb146b6a3d) | INCONCLUSIVE / DECISION_NOT_RECORDED | held |
| lifecycle | `file:DS04` | [`0x84d6e4d7...`](https://explorer-studio.genlayer.com/tx/0x84d6e4d7d8b7152ce40c2e3bfff17bc5e398816fb7c73423b1c1c33d0a21c08d) | submit_case FINALIZED/SUCCESS |  |
| success | `resolve:DS04` | [`0xf3c1a38f...`](https://explorer-studio.genlayer.com/tx/0xf3c1a38f9735b4249bcfb46595329cdef73e541a9d68bed4bda5228663b17e42) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| lifecycle | `file:DS05` | [`0x808dce78...`](https://explorer-studio.genlayer.com/tx/0x808dce784c6f6a53e1d365d9ad47aef1617e7a722d878eafbc2a25478c27a567) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS05` | [`0x534fb3fc...`](https://explorer-studio.genlayer.com/tx/0x534fb3fcf7d440e2422b14d158f9e1cbabe9bf3bd61a0a4be96db87e0f26cd62) | INCONCLUSIVE / CRITERIA_CONFLICT | held |
| lifecycle | `file:DS06` | [`0x3a2ef1b4...`](https://explorer-studio.genlayer.com/tx/0x3a2ef1b4ddd949e7d58a3190cb02758ed21f68541a49be9e50dc52e14cfbce7e) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS06` | [`0x1c255b61...`](https://explorer-studio.genlayer.com/tx/0x1c255b61511e4b007f1325ed09701b7473d6806b12d12d777a963b2ffdd4822b) | INCONCLUSIVE / EVIDENCE_CONTRADICTORY | held |
| lifecycle | `file:DS07` | [`0x88a0c067...`](https://explorer-studio.genlayer.com/tx/0x88a0c06778c854b1a5a549d7b6b7919b77534b17b49d64fc2f346e433bda21fa) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS07` | [`0x86e66251...`](https://explorer-studio.genlayer.com/tx/0x86e66251e8ff13bc52758ff7cc7e3bcaae8e2562da02eaef4255a64521e033c8) | INCONCLUSIVE / SOURCE_ADDRESSES_ADJUDICATOR | held |
| lifecycle | `file:DS08` | [`0xe184bc8c...`](https://explorer-studio.genlayer.com/tx/0xe184bc8cfaa67ca2542783163661dd677235326725cc380ffbd67025371fbf93) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS08` | [`0x05c7b28a...`](https://explorer-studio.genlayer.com/tx/0x05c7b28ab7846ba7ffc9884e5253df91f465eea9c210d4ee1e121b001bb96e13) | EVIDENCE_UNAVAILABLE / EVIDENCE_DIGEST_MISMATCH | held |
| lifecycle | `file:DS09` | [`0xa5cae298...`](https://explorer-studio.genlayer.com/tx/0xa5cae2986e3aaeb7ff83c915326a16498cfacf3f3798546d7bf2a179ab2e03f7) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS09` | [`0x6b06a645...`](https://explorer-studio.genlayer.com/tx/0x6b06a64565708285b1f583b3a56d23a5a6353d3fb95c01667315d891cdd91abc) | EVIDENCE_UNAVAILABLE / REQUIRED_EVIDENCE_UNREADABLE | held |
| lifecycle | `file:DS10` | [`0xdb846086...`](https://explorer-studio.genlayer.com/tx/0xdb846086216e9b441aa2975367ad82ca955fbc75f0373d49c5e68f7aeb84c71d) | submit_case FINALIZED/SUCCESS |  |
| negative | `resolve:DS10` | [`0x0a2a5e4e...`](https://explorer-studio.genlayer.com/tx/0x0a2a5e4e9633521bea82a49b7eac09e3ae95c3089d16ec3ba3d89a8d3210230d) | INCONCLUSIVE / BYTES_NOT_BOUND | held |
| success | `finalize:DS01` | [`0x9f1f1de3...`](https://explorer-studio.genlayer.com/tx/0x9f1f1de3a391f0572929a0fc9812ff71503ed0a494630dd0b9527803999567b6) | FINAL; is_policy_violation_confirmed confirmed=true, final=true | held |
| success | `finalize:DS02` | [`0xf3f6d95b...`](https://explorer-studio.genlayer.com/tx/0xf3f6d95b129aeeffb073c2348afc242fe205f6462acc7f768b3c14df4f9dac91) | FINAL; is_policy_violation_confirmed confirmed=false, final=true | held |
| lifecycle | `lapse:DS11` | [`0x7a794f11...`](https://explorer-studio.genlayer.com/tx/0x7a794f110f3843abaa6e221add30934d512caadf64845dd0eb143ed2fee6082d) | CANCELLED / LAPSED | held |
| lifecycle | `lapse:DS09` | [`0xce30bd4b...`](https://explorer-studio.genlayer.com/tx/0xce30bd4ba1e44513aafc79dee8105dd4f656ff0f45f4baeda3ad7b0c2f3a8039) | FINAL; EVIDENCE_UNAVAILABLE / REQUIRED_EVIDENCE_UNREADABLE | held |
| lifecycle | `refile:DS09` | [`0xa345fb5d...`](https://explorer-studio.genlayer.com/tx/0xa345fb5d1fa213a46a27332597f2f0e65f9726b6bb182943f41833d491fbac03) | a new case from the same tester: DC-000012 | held |
| negative | `refuse:stale_policy_version` | [`0x08656bec...`](https://explorer-studio.genlayer.com/tx/0x08656bec56f7a9c433e01887a38da72da0ad47664974c14f58d5d175993bd744) | refused: policy_version is not the version this challenge judges under: 2026-09 | held |
| negative | `refuse:policy_hash_mismatch` | [`0x98393dbc...`](https://explorer-studio.genlayer.com/tx/0x98393dbc0c5694b3ac81f00633e22df2886477b7b18cf4e3eb8e10c1764e051a) | refused: policy_sha256 does not match the challenge's policy document | held |
| negative | `refuse:personal_identifier` | [`0xb96e798d...`](https://explorer-studio.genlayer.com/tx/0xb96e798d087ddd3d349c2ab2d643758bb1aad0fb5d08dd9310123884aa2525ac) | refused: subject_reference must not contain a long digit sequence (an account or ID number): use a synthetic reference | held |
| negative | `refuse:email_in_summary` | [`0x651a7a5f...`](https://explorer-studio.genlayer.com/tx/0x651a7a5f8590017d8231bc87a931f661ef64aa5393334d21f524c0e0903b8cb2) | refused: input_summary must not contain an email address: use a synthetic reference | held |
| negative | `refuse:outside_domains` | [`0xab8d53fd...`](https://explorer-studio.genlayer.com/tx/0xab8d53fda602ecad36777c5d0f05bc89122b2ea2971e1df2bb8ea4b7b5fd1298) | refused: evidence[0] host is outside the challenge's evidence domains | held |
| negative | `refuse:explanation_addresses_adjudicator` | [`0xdc8b2494...`](https://explorer-studio.genlayer.com/tx/0xdc8b24940ce96b3ad4523b16e4f87397a1738491ca6dee5eb9f5649728f1579b) | refused: decision_explanation must not contain instructions to the evaluator or hidden text | held |
| negative | `refuse:second_case_same_tester` | [`0x3026a2b1...`](https://explorer-studio.genlayer.com/tx/0x3026a2b1229ac09f0a89eaf126032d5d1f7942e7a50e9f402a51193e30319197) | refused: this account already filed DC-000004 against this challenge | held |
| negative | `refuse:cancel_with_cases` | [`0x4a2cf5d7...`](https://explorer-studio.genlayer.com/tx/0x4a2cf5d771f4307e1ac68515b5552528118e9ac3d05bc90c769b3e43d80d485a) | refused: this challenge already has cases and cannot be cancelled; it closes at its deadline | held |
| negative | `refuse:double_resolution` | [`0x11c6721c...`](https://explorer-studio.genlayer.com/tx/0x11c6721c6c64263363d6b5a10c50bb78037460698d162bfb927c7c806924548f) | refused: only a PENDING case is resolved | held |
| negative | `refuse:stranger_contest` | [`0x2fa3cfb2...`](https://explorer-studio.genlayer.com/tx/0x2fa3cfb28041ff0f8f58f448cf9055172c14b6b05cf6b772199991bceed71c2f) | refused: only the tester or the challenge's publisher contests a verdict | held |
| negative | `refuse:stranger_withdraw` | [`0x2f544bd7...`](https://explorer-studio.genlayer.com/tx/0x2f544bd79896541eda251e150ad312ce778c99f61343cd7196c3e14edb4f3a4f) | refused: only the tester withdraws their own case | held |

## Mutation sweeps

| Sweep | Result |
|---|---|
| `deploy/mutation_sweep_first.txt` - the first sweep, on v0.1.0, before the tests it asked for | 85 mutations, 80 killed, 5 survived |
| `deploy/mutation_sweep_v1.txt` - v0.1.0 and its final suite | 85 mutations, 85 killed, 0 survived |
| `deploy/mutation_sweep_v2_first.txt` - the first sweep of v0.2.1 | 110 mutations, 109 killed, 1 survived |
| `deploy/mutation_sweep.txt` - the sweep of record, on the canonical v0.2.1 contract and the final suite | 110 mutations, **110 killed, 0 survived** |

Every survivor of the first sweep was a gap in the tests, and each now has the
test that kills it: a prohibited factor, and separately a contradicted
explanation, beside an unmet violation condition must not read as compliance
(both are `CRITERIA_CONFLICT`); an IP literal is refused as an evidence host; a
case cannot be filed against a cancelled challenge; and the record of a `LIVE`
item keeps only its status, never a digest or byte count that validators did not
compare. The 25 mutations added since v0.1.0 each break one fix from the
adversarial review or the fifth pass, and each is killed by the test written for
that fix in `tests/direct/test_ds_review.py`. The one survivor of the first
v0.2.1 sweep was an older test the new two-item rule had quietly disarmed: it
quoted the explanation alone, which the new rule refuses for a second reason,
so the mutation it was written to catch no longer changed its outcome. It now
quotes the explanation beside a real item.
