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
| Contract | [`0xc95E80E2a1bDe77A2e8aCB18fcaa374a6385cBf0`](https://explorer-studio.genlayer.com/address/0xc95E80E2a1bDe77A2e8aCB18fcaa374a6385cBf0) |
| Deployment transaction | [`0xa3a034eed9ec7c91230005474c1a861897eb1aa395025190a426c8b476057509`](https://explorer-studio.genlayer.com/tx/0xa3a034eed9ec7c91230005474c1a861897eb1aa395025190a426c8b476057509) |
| Status | FINALIZED, leader execution SUCCESS, votes AGREE x3 (two validators idle) |
| Source commit | `8f571fc04fa43540cb64d47cca95cb455cb176fa` |
| Contract blob | `4e433e0389281747ad45bd792d3602c37214df3d` |
| Source | byte-identical to the repository (sha256 `5f8fb800...5529`, in `deploy/deployment.json`) |
| Schema | 24 methods (16 view, 8 write), read from the chain |

## How the live evidence was reached

Two passes ran before the run of record. Both are kept under
`deploy/diagnostics/`.

| Pass | Deployment | What it found | What changed |
|---|---|---|---|
| `pass1_superseded_0x99612d2d` | first, `0x99612D2D` | the clearest violating case (DS01) read `INCONCLUSIVE` / `EVIDENCE_CONTRADICTORY`, and the publisher's contest repeated it: the panel counted the system's own false explanation - a ratio problem the inputs do not show - as evidence contradicting the inputs. The pass was stopped there | **the contract**: an explanation is a claim, not evidence, so contradictory evidence may no longer be quoted from it and the consistency subject is asked about the evidence items only; redeployed, the first deployment moved to `deploy/superseded/0x99612d2d/` |
| `pass2_0xc95e80e2` | canonical | 37 transactions, 14 of 14 outcomes held, 11 of 11 refused | nothing |

The lesson is in the first row. The design already said an explanation is a
claim about a decision and never evidence for it, and enforced that for every
finding a verdict rests on - except one: the consistency check. A lying
explanation is exactly what a violating case looks like, so if it counts as
"contradictory evidence", the cases DecisionShield exists to catch become
inconclusive. The false explanation now has one place to be read: the
`EXPLANATION` subject, where it is a criterion of the verdict.

## Live run of record

`python scripts/live_run.py` against the canonical deployment, 2026-10-02
22:00:25Z to 22:39:31Z, every evidence document served from
`raw.githubusercontent.com` at commit `10c852c`, from fourteen accounts:
a publisher, a keeper, a stranger and eleven testers, one per case.

**37 transactions, 14 of 14 outcomes held, 11 of 11 refusals refused.** Every
verdict the contract can store was reached on chain: a decline the policy forbade,
resting on the age band, `POLICY_VIOLATION_CONFIRMED` with severity `HIGH`, and
upheld by the publisher's contest; a lawful decline `POLICY_COMPLIANT`; an
approval talked out of a model by the applicant's own note confirmed as a
violation; four distinct `INCONCLUSIVE` reasons; a wrong digest and an
unpublished decision record each `EVIDENCE_UNAVAILABLE`; two verdicts finalized
and read back through `is_policy_violation_confirmed`; a lapse; and eleven
refusals, each for the reason it was sent to test.

| Step | Transaction | Recorded | |
|---|---|---|---|
| `challenge:credit-line` | [`0xb74d7a85...`](https://explorer-studio.genlayer.com/tx/0xb74d7a858a704575472a7082c25721d5e5c3bc14013a4a300b832e03cfc5500b) | publish_challenge FINALIZED/SUCCESS |  |
| `file:DS11` | [`0x14125436...`](https://explorer-studio.genlayer.com/tx/0x141254366f8a017094ba6ec82eb0658d04f869b591ecbd600b5293d5ebfdbb2f) | submit_case FINALIZED/SUCCESS |  |
| `file:DS01` | [`0x4e3d1156...`](https://explorer-studio.genlayer.com/tx/0x4e3d1156a87f6cda8ee2886b208698393a570731fb8559d04918e914fbaef7c6) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS01` | [`0x1b8a4837...`](https://explorer-studio.genlayer.com/tx/0x1b8a48376a1c7d72cd957d3dfb900526bd79c03d281049f297c92fc38052246b) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| `contest:DS01` | [`0xf6520bca...`](https://explorer-studio.genlayer.com/tx/0xf6520bca852c79814a3b8ecbc3943b2a41ad77375c70b2bafa52a813d4b903b5) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| `file:DS02` | [`0x4e73f7b3...`](https://explorer-studio.genlayer.com/tx/0x4e73f7b3f8885c4f96a1167392b26b7652458659a011299f8a4a4dfb4eceed9e) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS02` | [`0xcfe09406...`](https://explorer-studio.genlayer.com/tx/0xcfe094060d9638d04679a9e6ab947983d6fc359ecea4b28a51c2c7139adb13cf) | POLICY_COMPLIANT / RULE_FOLLOWED | held |
| `file:DS03` | [`0xb0923ad7...`](https://explorer-studio.genlayer.com/tx/0xb0923ad7aca5205b48b6ae1d026a138861ec8af014dce32c3dfcdcfa941fdeae) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS03` | [`0xa6970356...`](https://explorer-studio.genlayer.com/tx/0xa69703566b65becac05ae395fe644fac59f40e403048dacd2232e03d81d2e70a) | INCONCLUSIVE / DECISION_NOT_RECORDED | held |
| `file:DS04` | [`0x2a0eaff4...`](https://explorer-studio.genlayer.com/tx/0x2a0eaff46e2385b1156d8287eb2774840513a9a6f444951c5d099c69568cf44f) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS04` | [`0x8f885bb0...`](https://explorer-studio.genlayer.com/tx/0x8f885bb09b4e19e14ea8cb74312355fa3281c181d68b180e31a2ed0b5873e692) | POLICY_VIOLATION_CONFIRMED / VIOLATION_CONDITION_MET | held |
| `file:DS05` | [`0xa65bdadf...`](https://explorer-studio.genlayer.com/tx/0xa65bdadf99b8f84746804ae8a4c0ccc55b64a641facbfc3d82627178b498e9e2) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS05` | [`0x3179bcc9...`](https://explorer-studio.genlayer.com/tx/0x3179bcc937d5303380d5e2cfb6bfb6da408d1b0f99e27f16909c799129a78ec3) | INCONCLUSIVE / CRITERIA_CONFLICT | held |
| `file:DS06` | [`0xb6d43a5a...`](https://explorer-studio.genlayer.com/tx/0xb6d43a5a9c7df379807c4d76ce2f5001c763bb51c2bbb55fa0b3f43400a6a76e) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS06` | [`0xd9a07eb7...`](https://explorer-studio.genlayer.com/tx/0xd9a07eb7c182f5a7bcd0fd74a66a8b37c91a854544a506ebe2cd83fed284d812) | INCONCLUSIVE / EVIDENCE_CONTRADICTORY | held |
| `file:DS07` | [`0x28cc4e35...`](https://explorer-studio.genlayer.com/tx/0x28cc4e35347e473947868351f8d0d5fca236260c5bc7a8aa2e024893f880a471) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS07` | [`0x1b4d25a7...`](https://explorer-studio.genlayer.com/tx/0x1b4d25a7e0105ee753e336ad0b9295d7e162a1b2ba009bf70aa4a110eae41c4a) | INCONCLUSIVE / SOURCE_ADDRESSES_ADJUDICATOR | held |
| `file:DS08` | [`0x3ad162da...`](https://explorer-studio.genlayer.com/tx/0x3ad162da44f09e829912c5e8782a079a1681451173cc584d4d3bf511a495a79e) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS08` | [`0xb71d74f6...`](https://explorer-studio.genlayer.com/tx/0xb71d74f6eb16c6dec34253f88e7f62e64ad9d410f23a37d9c52a9d1bc924f28c) | EVIDENCE_UNAVAILABLE / EVIDENCE_DIGEST_MISMATCH | held |
| `file:DS09` | [`0x626a6244...`](https://explorer-studio.genlayer.com/tx/0x626a62441165d6e46f3c7e05706797f4e21a94c15afe440ee86f6d67020824b4) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS09` | [`0x90bf2776...`](https://explorer-studio.genlayer.com/tx/0x90bf2776da7de75e8ad499bb8576aee4a7dbefb92faa5115554793a75f23efb9) | EVIDENCE_UNAVAILABLE / REQUIRED_EVIDENCE_UNREADABLE | held |
| `file:DS10` | [`0xc72d1a84...`](https://explorer-studio.genlayer.com/tx/0xc72d1a84b2d1336675802c6a198fc9a6ddacd6f49163bceb9c68c5ae0e2bbb97) | submit_case FINALIZED/SUCCESS |  |
| `resolve:DS10` | [`0xc0ce36e8...`](https://explorer-studio.genlayer.com/tx/0xc0ce36e8414a464ae6430d5e65a4de43b53d578adff1a5e4d22b7673b233feae) | INCONCLUSIVE / BYTES_NOT_BOUND | held |
| `finalize:DS01` | [`0x4252cde1...`](https://explorer-studio.genlayer.com/tx/0x4252cde1229d77d868eec42d7d95dc75755d9652e90e044a07fffd523fe902ac) | FINAL; is_policy_violation_confirmed confirmed=true, final=true | held |
| `finalize:DS02` | [`0xe1c90bc4...`](https://explorer-studio.genlayer.com/tx/0xe1c90bc46f07ff3c44ec4e9223927c4f3ccd3f57d38ec7615283575e6f8f35ec) | FINAL; is_policy_violation_confirmed confirmed=false, final=true | held |
| `lapse:DS11` | [`0xb607443a...`](https://explorer-studio.genlayer.com/tx/0xb607443a190d071c35463595cd8b3c63fad9c55133c545b382ce3131ba52a256) | CANCELLED / LAPSED | held |
| `refuse:stale_policy_version` | [`0xd8d59b7b...`](https://explorer-studio.genlayer.com/tx/0xd8d59b7bf22955dc37e3e00ad1ceb31b504962ab48afbcd562be182f8e2f5540) | refused: policy_version is not the version this challenge judges under: 2026-09 | held |
| `refuse:policy_hash_mismatch` | [`0x3ca3e7b2...`](https://explorer-studio.genlayer.com/tx/0x3ca3e7b20dbbba0f5d5f5d71136871525991aa17a3a209024d164ddbfe3e23e7) | refused: policy_sha256 does not match the challenge's policy document | held |
| `refuse:personal_identifier` | [`0xf962eff3...`](https://explorer-studio.genlayer.com/tx/0xf962eff3c23f82c5a6617bb81dc1ffc547a6b6833868c98a06322e4426d8f46f) | refused: subject_reference must not contain a long digit sequence (an account or ID number): use a synthetic reference | held |
| `refuse:email_in_summary` | [`0x3e89405b...`](https://explorer-studio.genlayer.com/tx/0x3e89405bcca1079d33179c6afe7a9d94a6326b23c71884e911b679f84fbff96e) | refused: input_summary must not contain an email address: use a synthetic reference | held |
| `refuse:outside_domains` | [`0x80981029...`](https://explorer-studio.genlayer.com/tx/0x809810299027fc6ac122be154bfbb6af2a22ec7a6b7e67288e46011c12ecdade) | refused: evidence[0] host is outside the challenge's evidence domains | held |
| `refuse:explanation_addresses_adjudicator` | [`0xd9741bdc...`](https://explorer-studio.genlayer.com/tx/0xd9741bdc18ab6e53835e1f63a00a030be2138a9a6453dd7880e6c8524c9961e4) | refused: decision_explanation must not contain instructions to the evaluator or hidden text | held |
| `refuse:second_case_same_tester` | [`0x489712d5...`](https://explorer-studio.genlayer.com/tx/0x489712d53b571e81e3527f5260fc7d51fe678860ad6e9e3ed3c004838174780f) | refused: this account already filed DC-000015 against this challenge | held |
| `refuse:cancel_with_cases` | [`0xbcdd9b92...`](https://explorer-studio.genlayer.com/tx/0xbcdd9b92dadfae83bc70cfcf6cbb240a7c01ebeaba5349c871bad481e562e2d5) | refused: this challenge already has cases and cannot be cancelled; it closes at its deadline | held |
| `refuse:double_resolution` | [`0x6d99ca27...`](https://explorer-studio.genlayer.com/tx/0x6d99ca272153639b4cc07841006b8f8d5b7447e192176f10e746d4a674ae5493) | refused: only a PENDING case is resolved | held |
| `refuse:stranger_contest` | [`0xc18295ef...`](https://explorer-studio.genlayer.com/tx/0xc18295efe79b4bbf85a6cc6bf8d405ff590cda4d984c9962f41ea47e7db6f034) | refused: only the tester or the challenge's publisher contests a verdict | held |
| `refuse:stranger_withdraw` | [`0xd09c2ead...`](https://explorer-studio.genlayer.com/tx/0xd09c2eadf4971273d63356628a4e8f4d5bac1ca4badfd8bb761a0a498ed8c270) | refused: only the tester withdraws their own case | held |

## Mutation sweeps

| Sweep | Result |
|---|---|
| `deploy/mutation_sweep_first.txt` - the first sweep, before the tests it asked for | 85 mutations, 80 killed, 5 survived |
| `deploy/mutation_sweep.txt` - the sweep of record, on the canonical contract and the final suite | 85 mutations, **85 killed, 0 survived** |

Every survivor of the first sweep was a gap in the tests, and each now has the
test that kills it: a prohibited factor, and separately a contradicted
explanation, beside an unmet violation condition must not read as compliance
(both are `CRITERIA_CONFLICT`); an IP literal is refused as an evidence host; a
case cannot be filed against a cancelled challenge; and the record of a `LIVE`
item keeps only its status, never a digest or byte count that validators did not
compare.
