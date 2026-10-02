"""The lifecycle, the verdicts and the views a consumer reads."""

from tests.direct import support as s

LATER = "2026-10-02T14:00:00Z"


def verdict(ds, submission_id) -> tuple:
    v = ds.get_verdict(submission_id)
    return (v["verdict"], v["reason_code"])


# -- the challenge -------------------------------------------------------------

def test_a_challenge_is_published_with_its_hashes(ds, direct_vm, direct_alice, mod):
    challenge_id = s.published(ds, direct_vm, direct_alice)
    info = ds.get_challenge(challenge_id)
    assert info["found"] and challenge_id == "DS-000001"
    assert info["publisher"] == direct_alice.as_hex.lower()
    assert info["definition_hash"] == mod._sha256_hex(mod._canonical(info["challenge"]))
    hashes = ds.get_policy_hash(challenge_id)
    assert hashes["policy_sha256"] == s.digest(s.POLICY)
    assert hashes["policy_version"] == "2026-09"
    assert ds.get_policy_version(challenge_id)["policy_url"] == s.POLICY_URL


def test_a_challenge_closes_at_its_deadline(ds, direct_vm, direct_alice):
    challenge_id = s.published(ds, direct_vm, direct_alice)
    assert ds.get_challenge_status(challenge_id, s.NOW)["accepting_cases"] is True
    late = ds.get_challenge_status(challenge_id, "2026-10-10T00:00:00Z")
    assert late["effective_status"] == "CLOSED" and late["accepting_cases"] is False


def test_a_challenge_with_no_cases_can_be_cancelled(ds, direct_vm, direct_alice, direct_bob):
    challenge_id = s.published(ds, direct_vm, direct_alice)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only the challenge's publisher"):
        ds.cancel_challenge(challenge_id)
    direct_vm.sender = direct_alice
    assert ds.cancel_challenge(challenge_id) == "CANCELLED"


def test_a_challenge_with_a_case_cannot_be_cancelled(ds, direct_vm, direct_alice,
                                                     direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    s.filed(ds, direct_vm, direct_bob, challenge_id)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("already has cases"):
        ds.cancel_challenge(challenge_id)


def test_get_config_publishes_the_vocabulary(ds):
    config = ds.get_config()
    assert config["payable"] is False
    assert config["verdicts"] == ["PENDING", "POLICY_VIOLATION_CONFIRMED", "POLICY_COMPLIANT",
                                  "INCONCLUSIVE", "EVIDENCE_UNAVAILABLE", "CANCELLED"]
    assert config["evidence_roles"] == ["POLICY", "CASE_INPUT", "MODEL_OUTPUT",
                                        "EXPLANATION", "CORROBORATION"]
    assert set(config["code_reasons"]) <= set(config["reason_codes"])


# -- the case ------------------------------------------------------------------

def test_a_case_commits_to_the_challenge_and_the_policy(ds, direct_vm, direct_alice,
                                                        direct_bob, mod):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id = s.filed(ds, direct_vm, direct_bob, challenge_id)
    sub = ds.get_submission(submission_id)
    assert sub["found"] and submission_id == "DC-000001"
    assert sub["tester"] == direct_bob.as_hex.lower()
    assert [i["evidence_id"] for i in sub["evidence"]] == ["P", "E1", "E2", "E3"]
    assert sub["evidence"][0]["role"] == "POLICY"
    assert sub["evidence"][0]["sha256"] == s.digest(s.POLICY)
    assert sub["explanation_is_a_claim"] is True
    assert sub["evidence_commitment"] == mod._sha256_hex(mod._canonical(sub["evidence"]))


def test_a_stale_policy_is_refused(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    with direct_vm.expect_revert("policy_version is not the version"):
        s.filed(ds, direct_vm, direct_bob, challenge_id, policy_version="2026-06")
    with direct_vm.expect_revert("policy_sha256 does not match"):
        s.filed(ds, direct_vm, direct_bob, challenge_id, policy_sha256="00" * 32)
    with direct_vm.expect_revert("challenge_hash does not match"):
        s.filed(ds, direct_vm, direct_bob, challenge_id, challenge_hash="00" * 32)


def test_one_case_per_tester_per_challenge(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    first = s.filed(ds, direct_vm, direct_bob, challenge_id)
    with direct_vm.expect_revert("already filed " + first):
        s.filed(ds, direct_vm, direct_bob, challenge_id)


def test_a_case_after_the_deadline_is_refused(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    direct_vm.warp("2026-10-10T00:00:00Z")
    with direct_vm.expect_revert("the submission deadline passed"):
        s.filed(ds, direct_vm, direct_bob, challenge_id)


def test_only_the_tester_withdraws(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id = s.filed(ds, direct_vm, direct_bob, challenge_id)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("only the tester withdraws"):
        ds.withdraw_case(submission_id)
    direct_vm.sender = direct_bob
    assert ds.withdraw_case(submission_id) == "CANCELLED"
    assert ds.get_submission(submission_id)["reason_code"] == "WITHDRAWN"


# -- the verdicts --------------------------------------------------------------

def test_a_violation_is_confirmed_with_the_challenges_severity(ds, direct_vm, direct_alice,
                                                               direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, resolution_id = s.resolved(ds, direct_vm, direct_bob, challenge_id)
    v = ds.get_verdict(submission_id)
    assert (v["verdict"], v["reason_code"]) == ("POLICY_VIOLATION_CONFIRMED",
                                                "VIOLATION_CONDITION_MET")
    assert v["severity"] == "HIGH" and v["policy_compliant"] is False
    assert v["evidence_status"] == "EVIDENCE_REACHABLE"
    assert v["criteria"] == {"decision_recorded": True, "violation_condition_met": True,
                             "rule_followed": False, "prohibited_factor_detected": True,
                             "explanation_supported": False}
    assert v["policy_sha256"] == s.digest(s.POLICY)
    rec = s.record_of(ds, resolution_id)
    assert all(f["compared"] for f in rec["findings"])
    assert ds.is_policy_violation_confirmed(submission_id)["confirmed"] is True
    assert ds.get_stats()["violations_confirmed"] == 1


def test_a_compliant_decision_is_recorded_as_such(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages=s.COMPLIANT_PAGES)
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                   subjects=s.compliant_said(), items=s.compliant_items())
    v = ds.get_verdict(submission_id)
    assert (v["verdict"], v["reason_code"]) == ("POLICY_COMPLIANT", "RULE_FOLLOWED")
    assert v["severity"] == "" and v["policy_compliant"] is True
    assert v["criteria"]["rule_followed"] is True
    assert ds.is_policy_violation_confirmed(submission_id)["confirmed"] is False


def test_no_prohibited_factors_means_none_assessed(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages=s.COMPLIANT_PAGES,
                               prohibited_factors=[])
    subjects = s.compliant_said()
    del subjects["PROHIBITED_FACTOR"]
    submission_id, resolution_id = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                              subjects=subjects, items=s.compliant_items())
    assert verdict(ds, submission_id) == ("POLICY_COMPLIANT", "RULE_FOLLOWED")
    assert ds.get_verdict(submission_id)["criteria"]["prohibited_factor_detected"] is None
    assert "PROHIBITED_FACTOR" not in [f["id"] for f in s.record_of(ds, resolution_id)
                                       ["findings"]]


def test_a_tampered_document_is_evidence_unavailable(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    items = s.usual_items(output_body=s.OUTPUT + " ")
    submission_id, resolution_id = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                              items=items)
    assert verdict(ds, submission_id) == ("EVIDENCE_UNAVAILABLE", "EVIDENCE_DIGEST_MISMATCH")
    assert ds.get_verdict(submission_id)["evidence_status"] == "EVIDENCE_UNAVAILABLE"
    assert s.source_in(s.record_of(ds, resolution_id), "E2")["status"] == "DIGEST_MISMATCH"


def test_a_policy_that_changed_since_the_challenge_is_evidence_unavailable(
        ds, direct_vm, direct_alice, direct_bob):
    edited = s.page("Fixture Lender credit line policy 2026-09", [s.RULE_LINE])
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages={s.POLICY_URL: edited})
    submission_id, resolution_id = s.resolved(ds, direct_vm, direct_bob, challenge_id)
    assert verdict(ds, submission_id) == ("EVIDENCE_UNAVAILABLE", "EVIDENCE_DIGEST_MISMATCH")
    assert s.source_in(s.record_of(ds, resolution_id), "P")["status"] == "DIGEST_MISMATCH"


def test_an_unpublished_policy_is_evidence_unavailable(ds, direct_vm, direct_alice,
                                                       direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages={s.POLICY_URL: None})
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id)
    assert verdict(ds, submission_id) == ("EVIDENCE_UNAVAILABLE", "POLICY_UNREADABLE")


def test_a_required_role_that_cannot_be_read_is_evidence_unavailable(ds, direct_vm,
                                                                     direct_alice,
                                                                     direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages={s.OUTPUT_URL: None})
    submission_id, resolution_id = s.resolved(ds, direct_vm, direct_bob, challenge_id)
    assert verdict(ds, submission_id) == ("EVIDENCE_UNAVAILABLE",
                                          "REQUIRED_EVIDENCE_UNREADABLE")
    assert s.record_of(ds, resolution_id)["panel_state"] == "SKIPPED"


def test_a_document_addressing_the_adjudicator_stops_the_round(ds, direct_vm, direct_alice,
                                                               direct_bob):
    poisoned = s.record("case-input", [s.DTI_LINE, s.DEFAULT_LINE, s.INJECTION])
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages={s.CASE_URL: poisoned})
    submission_id, resolution_id = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                              items=s.usual_items(case_body=poisoned))
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "SOURCE_ADDRESSES_ADJUDICATOR")
    assert s.record_of(ds, resolution_id)["markers"] == ["E1:BODY"]


def test_an_attack_on_the_financial_ai_stays_adjudicable(ds, direct_vm, direct_alice,
                                                         direct_bob):
    """An applicant's attempt to manipulate the underwriting model is the evidence
    under test, not an attack on this panel: it does not stop the round."""
    crafted = s.record("case-input", [s.HIGH_DTI_LINE, s.DEFAULT_LINE,
                                      s.APPLICANT_INJECTION])
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice,
                               pages={s.CASE_URL: crafted, s.OUTPUT_URL: s.APPROVE_OUTPUT})
    items = s.usual_items(case_body=crafted, output_body=s.APPROVE_OUTPUT)
    subjects = s.violation_said(
        violation="MET", rule="BROKEN", factor="NOT_USED", explanation="SUPPORTED",
        quotes={"DECISION_RECORDED": [("E2", s.APPROVE_LINE)],
                "VIOLATION_CONDITION": [("E1", s.APPLICANT_INJECTION), ("E2", s.APPROVE_LINE)],
                "DECISION_RULE": [("E1", s.HIGH_DTI_LINE), ("E2", s.APPROVE_LINE)]})
    submission_id, resolution_id = s.resolved(
        ds, direct_vm, direct_bob, challenge_id, subjects=subjects, items=items,
        ai_decision="APPROVE", claimed_violation="ADVERSARIAL_INPUT")
    assert s.record_of(ds, resolution_id)["markers"] == []
    assert verdict(ds, submission_id) == ("POLICY_VIOLATION_CONFIRMED",
                                          "VIOLATION_CONDITION_MET")


def test_an_unusable_answer_is_inconclusive(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id = s.filed(ds, direct_vm, direct_bob, challenge_id)
    direct_vm._llm_mocks.clear()
    direct_vm.mock_llm("DecisionShield adjudication panel", "The model seems biased.")
    ds.resolve(submission_id)
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "PANEL_UNUSABLE")


def test_contradictory_evidence_is_inconclusive(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, resolution_id = s.resolved(
        ds, direct_vm, direct_bob, challenge_id,
        subjects=s.violation_said(consistency="CONTRADICTORY"))
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "EVIDENCE_CONTRADICTORY")
    assert ds.get_verdict(submission_id)["evidence_status"] == "EVIDENCE_CONTRADICTORY"
    compared = {f["id"]: f["compared"] for f in s.record_of(ds, resolution_id)["findings"]}
    assert compared["EVIDENCE_CONSISTENCY"] is True and compared["DECISION_RULE"] is False


def test_unclear_consistency_is_inconclusive(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                   subjects=s.violation_said(consistency="UNCLEAR"))
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "CONSISTENCY_UNCLEAR")


def test_a_decision_the_output_does_not_record_is_inconclusive(ds, direct_vm, direct_alice,
                                                               direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, _r = s.resolved(
        ds, direct_vm, direct_bob, challenge_id, ai_decision="APPROVE",
        subjects=s.violation_said(decision="DIFFERS"))
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "DECISION_NOT_RECORDED")


def test_an_unclear_decision_or_violation_is_inconclusive(ds, direct_vm, direct_alice,
                                                          direct_bob, direct_charlie):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    a, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                       subjects=s.violation_said(decision="UNCLEAR"))
    assert verdict(ds, a) == ("INCONCLUSIVE", "DECISION_UNCLEAR")
    b, _r = s.resolved(ds, direct_vm, direct_charlie, challenge_id,
                       subjects=s.violation_said(violation="UNCLEAR"))
    assert verdict(ds, b) == ("INCONCLUSIVE", "VIOLATION_UNCLEAR")


def test_a_broken_rule_without_the_declared_violation_is_a_conflict(ds, direct_vm,
                                                                    direct_alice,
                                                                    direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                   subjects=s.violation_said(violation="NOT_MET"))
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "CRITERIA_CONFLICT")


def test_an_unclear_criterion_blocks_compliance(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages=s.COMPLIANT_PAGES)
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                   subjects=s.compliant_said(explanation="UNCLEAR"),
                                   items=s.compliant_items())
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "CRITERIA_UNCLEAR")


def test_a_violation_resting_on_unbound_bytes_is_inconclusive(ds, direct_vm, direct_alice,
                                                              direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    items = [s.item(s.CASE_URL, s.CASE, "Inputs", "CASE_INPUT", kind="LIVE"),
             s.item(s.OUTPUT_URL, s.OUTPUT, "Decision", "MODEL_OUTPUT", kind="LIVE")]
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id, items=items)
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "BYTES_NOT_BOUND")


def test_compliance_resting_on_unbound_bytes_is_inconclusive(ds, direct_vm, direct_alice,
                                                             direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages=s.COMPLIANT_PAGES)
    items = [s.item(s.CASE_URL, s.HIGH_DTI_CASE, "Inputs", "CASE_INPUT", kind="LIVE"),
             s.item(s.OUTPUT_URL, s.DTI_OUTPUT, "Decision", "MODEL_OUTPUT")]
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                   subjects=s.compliant_said(), items=items)
    assert verdict(ds, submission_id) == ("INCONCLUSIVE", "BYTES_NOT_BOUND")


# -- windows, contest, finality ------------------------------------------------

def test_an_unresolved_case_lapses(ds, direct_vm, direct_alice, direct_bob, direct_charlie):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id = s.filed(ds, direct_vm, direct_bob, challenge_id)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("the resolve window closes at"):
        ds.lapse_case(submission_id)
    direct_vm.warp(LATER)
    s.panel(direct_vm, s.violation_said())
    with direct_vm.expect_revert("the resolve window closed at"):
        ds.resolve(submission_id)
    assert ds.lapse_case(submission_id) == "CANCELLED"
    assert ds.get_submission(submission_id)["reason_code"] == "LAPSED"


def test_a_contest_is_a_second_reading_of_the_same_bytes(ds, direct_vm, direct_alice,
                                                         direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, first = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                      subjects=s.violation_said(violation="UNCLEAR"))
    s.panel(direct_vm, s.violation_said())
    direct_vm.sender = direct_alice
    second = ds.contest(submission_id)
    rec = s.record_of(ds, second)
    assert rec["mode"] == "CONTEST" and rec["round"] == 2 and rec["supersedes"] == first
    assert verdict(ds, submission_id)[0] == "POLICY_VIOLATION_CONFIRMED"
    with direct_vm.expect_revert("contested once already"):
        ds.contest(submission_id)


def test_only_the_tester_or_the_publisher_contests(ds, direct_vm, direct_alice, direct_bob,
                                                  direct_charlie):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("only the tester or the challenge's publisher"):
        ds.contest(submission_id)
    s.panel(direct_vm, s.violation_said(violation="UNCLEAR"))
    direct_vm.sender = direct_bob
    ds.contest(submission_id)
    assert ds.get_stats()["violations_confirmed"] == 0


def test_a_verdict_is_final_only_after_its_contest_window(ds, direct_vm, direct_alice,
                                                          direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id)
    assert ds.is_policy_violation_confirmed(submission_id)["final"] is False
    with direct_vm.expect_revert("the contest window closes at"):
        ds.finalize(submission_id)
    direct_vm.warp(LATER)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("the contest window closed at"):
        ds.contest(submission_id)
    assert ds.finalize(submission_id) == "FINAL"
    answer = ds.is_policy_violation_confirmed(submission_id)
    assert answer["confirmed"] is True and answer["final"] is True
    with direct_vm.expect_revert("only a RESOLVED case is finalized"):
        ds.finalize(submission_id)


def test_the_actions_and_evidence_views(ds, direct_vm, direct_alice, direct_bob):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id = s.filed(ds, direct_vm, direct_bob, challenge_id)
    assert ds.get_actions(submission_id, s.NOW)["may_resolve"] is True
    assert ds.get_actions(submission_id, LATER)["effective_status"] == "CANCELLED"
    before = ds.get_evidence_status(submission_id)
    assert [i["status"] for i in before["items"]] == ["", "", "", ""]
    s.panel(direct_vm, s.violation_said())
    ds.resolve(submission_id)
    after = ds.get_evidence_status(submission_id)
    assert [i["status"] for i in after["items"]] == ["RETRIEVED"] * 4
    assert after["evidence_status"] == "EVIDENCE_REACHABLE"
    assert ds.get_actions(submission_id, s.NOW)["may_contest"] is True
    assert ds.get_actions(submission_id, LATER)["may_finalize"] is True
    history = ds.get_history(submission_id)["rounds"]
    assert history[0]["severity"] == "HIGH"
