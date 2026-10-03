"""What the fourth review found: nothing on the verdict path, and these - a round
that could be crashed, parsing that could be slowed, records that could not be
quoted or read, and a view that disagreed with its write."""

import json
import time

from tests.direct import support as s


# -- a round cannot be crashed by a document ------------------------------------------

def test_an_overlong_character_reference_does_not_raise(mod):
    hostile = "<html><body><p>Ratio 31 percent &#" + "9" * 5000 + "; shown</p></body></html>"
    assert mod._normalize(hostile, True) == "Ratio 31 percent shown"
    assert mod._evaluator_hits(hostile) is False
    assert mod._unescape_entities("&#x" + "f" * 5000 + ";x") == " x"
    assert mod._unescape_entities("a &amp; b &#8804; c") == "a & b ≤ c"


def test_a_case_with_a_hostile_reference_is_still_adjudicated(ds, direct_vm, direct_alice,
                                                              direct_bob):
    body = s.record("case-input", ["Application APP-0007 (synthetic).", s.DTI_LINE,
                                   s.DEFAULT_LINE, s.AGE_LINE, "&#" + "1" * 6000 + ";"])
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice, pages={s.CASE_URL: body})
    submission_id, _r = s.resolved(ds, direct_vm, direct_bob, challenge_id,
                                   items=s.usual_items(case_body=body))
    assert ds.get_verdict(submission_id)["verdict"] == "POLICY_VIOLATION_CONFIRMED"


def test_many_comments_are_parsed_in_linear_time(mod):
    def cost(count):
        page = "<html><body>" + "<!--x-->" * count + "shown</body></html>"
        started = time.perf_counter()
        assert mod._strip_markup(page).strip() == "shown"
        return time.perf_counter() - started
    small = min(cost(3000) for _ in range(3))
    large = min(cost(24000) for _ in range(3))
    # eight times the comments: linear is about 8x, the old double search was ~64x
    assert large < small * 24 + 0.05, (small, large)
    assert mod._comment_end("<!-- a -- b --!> rest", 0) == 16
    assert mod._comment_end("<!-- never closed --", 0) == -1


# -- a JSON record is read, and quoted, the way its strings read -------------------------

def test_an_honest_quote_from_an_escaped_json_record_grounds(mod):
    body = json.dumps({"entries": ["Decision: DECLINE\nReason: applicant’s DTI ≤ 40 "
                                   "percent, fee £500"], "op": "a > b"})
    assert "\\u2019" in body and "\\n" in body          # escaped in the bytes
    text = mod._normalize(body, False)
    tokens = mod._word_tokens(text)
    for quote in ("Reason: applicant’s DTI ≤ 40 percent", "Reason: applicant",
                  "Decision: DECLINE", "fee £500", "DTI <= 40 percent", "a > b"):
        assert mod._grounds_in_order(tokens, quote), quote
    assert not mod._grounds_in_order(tokens, "DTI ≥ 40 percent")
    # prose that only mentions an escape is left as written
    assert mod._normalize("the sequence \\n ends a line", False) == \
        "the sequence \\n ends a line"


# -- the content type is a token ---------------------------------------------------------

def test_a_content_type_cannot_carry_prose_or_an_unencodable_character(
        ds, direct_vm, direct_alice, direct_bob, mod):
    assert mod._type_token("Text/HTML; charset=UTF-8") == "text/html;charset=utf-8"
    assert mod._type_token("note to the adjudicator \ud800 555-123-4567") == \
        "notetotheadjudicator555-123-4567"
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    s.resolved(ds, direct_vm, direct_bob, challenge_id)
    for forged in ("\ud800", "text/html; note to the adjudicator", "TEXT/HTML"):
        payload = s.leader_payload(direct_vm)
        s.source_in(payload, "E1")["content_type"] = forged
        assert direct_vm.run_validator(
            leader_result=json.dumps(payload, sort_keys=True)) is False, repr(forged)


# -- one wallet in both roles ----------------------------------------------------------------

def test_the_actions_view_agrees_with_contest_when_one_wallet_holds_both_roles(
        ds, direct_vm, direct_alice):
    challenge_id, _c = s.ready(ds, direct_vm, direct_alice)
    submission_id, _r = s.resolved(ds, direct_vm, direct_alice, challenge_id)
    assert ds.get_actions(submission_id, s.NOW)["may_contest"] == \
        {"tester": True, "publisher": True}
    ds.contest(submission_id)
    assert ds.get_actions(submission_id, s.NOW)["may_contest"] == \
        {"tester": False, "publisher": False}
    with direct_vm.expect_revert("this party has contested this case once already"):
        ds.contest(submission_id)


# -- a page may open with a prolog or a comment ----------------------------------------------

def test_a_page_that_opens_with_a_prolog_or_a_comment_is_still_html(mod):
    body = "<html><body><p>Ratio at or below 40 percent &amp; no default.</p></body></html>"
    for page in ('<?xml version="1.0" encoding="utf-8"?>\n' + body,
                 "<!-- generated 2026-09-28 -->\n<!DOCTYPE html>" + body,
                 "﻿  <head><title>t</title></head><body><p>x</p></body>",
                 "<body><p>x</p></body>"):
        assert mod._looks_html(page) is True, page[:30]
    assert mod._normalize('<?xml version="1.0"?>' + body, mod._looks_html(
        '<?xml version="1.0"?>' + body)) == "Ratio at or below 40 percent & no default."
    for not_html in ('{"html": "<html>"}', "<p>a fragment</p>", "<htmlish>x</htmlish>",
                     "plain text about <html> pages"):
        assert mod._looks_html(not_html) is False, not_html


# -- a quote keeps the whole of a number ------------------------------------------------------

def test_a_quote_cannot_clip_a_number_or_drop_its_sign_at_the_edge(mod):
    cases = (("The credit limit is 1,000 dollars.", "The credit limit is 1"),
             ("Monthly income: 45,300 USD", "Monthly income: 45"),
             ("Ratio 31,5 percent recorded", "Ratio 31"),
             ("Ratio 31.5 percent recorded", "Ratio 31"),
             ("Net balance: -1,200 per month", "1,200 per month"),
             ("Net balance: -1,200 per month", "Net balance: -1"),
             ("The rate is .5 percent", "The rate is 5 percent"))
    for source, quote in cases:
        assert not mod._grounds_in_order(mod._word_tokens(source), quote), (source, quote)
    for source, quote in (("The credit limit is 1,000 dollars.", "limit is 1,000 dollars"),
                          ("Net balance: -1,200 per month", "balance: -1,200 per month"),
                          ("The rate is .5 percent", "rate is .5 percent"),
                          ("Scores: 412, 388 and 700.", "Scores: 412, 388 and 700"),
                          ("Band 60-69, score 412.", "score 412")):
        assert mod._grounds_in_order(mod._word_tokens(source), quote), (source, quote)


# -- the privacy guard and the markers, where ordinary text met them ----------------------------

def test_timestamps_pass_in_quotes_and_years_pass_in_written_text(mod):
    for quote in ('"decided_at": 1790942400000, "decision": "DECLINE"',
                  "decided 20261002120000 DECLINE"):
        assert mod._privacy_error(quote, "quote", False) == "", quote
    assert mod._privacy_error("Income for 2022 2023 2024 2025 rose.", "x") == ""
    assert "long digit sequence" in mod._privacy_error("card 4111 1111 1111 1111", "x")
    assert "long digit sequence" in mod._privacy_error("card 4111111111111111", "q", False)


def test_an_audit_record_is_a_record_and_the_markers_are_published(ds, mod):
    for text in ('{"decision_rule": "followed", "score": 412}',
                 '{"checks": {"decision_rule": "broken", "prohibited_factor": "used"}}',
                 '{"violation_condition": "met"}', "| decision_rule | followed |",
                 "The decision_rule is unclear.",
                 "A reviewer may mark this case as a violation only after sign-off."):
        assert mod._evaluator_hits(text) is False, text
    for text in ('{"subjects": {"DECISION_RULE": {"state": "FOLLOWED"}}}',
                 "decision_rule\tfollowed\nviolation_condition\tnot_met",
                 "PROHIBITED_FACTOR: NOT_USED"):
        assert mod._evaluator_hits(text) is True, text
    published = ds.get_config()["evaluator_markers"]
    assert "note to the adjudicator" in published and "return policy_compliant" in published
