"""Reads against the canonical StudioNet deployment.

These tests do not re-run consensus: they check that the contract on chain is the
contract in this repository, that it answers, and that every verdict the live run
recorded is what the chain still holds - including through the view a monitoring
system would poll. One write is opt-in (`DS_LIVE_WRITES=1`).

Each test is independently runnable:

    python -m pytest tests/integration -q
    python -m pytest tests/integration -q -k source_is_this_repository
"""

import base64
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.request

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

RECORD = ROOT / "deploy" / "deployment.json"
TRANSCRIPT = ROOT / "deploy" / "live_run_transcript.json"
CONTRACT = ROOT / "contracts" / "decisionshield.py"
RPC = "https://studio.genlayer.com/api"

pytestmark = pytest.mark.skipif(not RECORD.exists(),
                                reason="no canonical deployment recorded yet")


def rpc(method: str, params: list):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params}).encode()
    request = urllib.request.Request(RPC, data=body, headers={
        "Content-Type": "application/json", "User-Agent": "ds-integration"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                answer = json.loads(response.read().decode())
            if "error" in answer and "-32029" in json.dumps(answer["error"]):
                raise RuntimeError("rate limited")
            return answer
        except Exception:
            if attempt == 5:
                raise
            time.sleep(5 * (attempt + 1))


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def client():
    """A read-only client with a throwaway account: nothing under .data/ is needed."""
    import studionet_transport  # noqa: F401 - retries RPC transport failures
    from genlayer_py import create_account, create_client
    from genlayer_py.chains import studionet
    return create_client(chain=studionet, account=create_account(), endpoint=RPC)


def read(client, record, method, args=None):
    return client.read_contract(address=record["contract_address"],
                                function_name=method, args=args or [])


def steps() -> dict:
    return json.loads(TRANSCRIPT.read_text(encoding="utf-8"))["steps"]


def test_the_deployed_source_is_this_repository(record):
    raw = rpc("gen_getContractCode", [record["contract_address"]]).get("result")
    deployed = str(raw).encode()
    if hashlib.sha256(deployed).hexdigest() != record["source_sha256"]:
        deployed = base64.b64decode(raw)
    assert hashlib.sha256(deployed).hexdigest() == record["source_sha256"]
    assert record["source_sha256"] == hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    assert record["byte_identical"] is True


def test_the_schema_is_the_whole_surface(record):
    schema = rpc("gen_getContractSchema", [record["contract_address"]]).get("result") or {}
    methods = schema.get("methods") or {}
    assert len(methods) == 24
    for name in ("publish_challenge", "submit_case", "resolve", "contest", "finalize",
                 "get_challenge", "get_submission", "get_verdict",
                 "is_policy_violation_confirmed", "get_policy_hash", "get_evidence_status",
                 "get_challenge_status", "get_policy_version"):
        assert name in methods, name


def test_the_config_on_chain_matches_the_contract(client, record):
    config = read(client, record, "get_config")
    assert config["payable"] is False
    assert config["verdicts"] == ["PENDING", "POLICY_VIOLATION_CONFIRMED", "POLICY_COMPLIANT",
                                  "INCONCLUSIVE", "EVIDENCE_UNAVAILABLE", "CANCELLED"]


@pytest.mark.skipif(not TRANSCRIPT.exists(), reason="no live run recorded yet")
def test_every_verdict_the_run_recorded_is_still_on_chain(client, record):
    checked = 0
    for name, entry in sorted(steps().items()):
        if not name.startswith(("resolve:", "contest:")) or "resolution_id" not in entry:
            continue
        resolution = read(client, record, "get_resolution", [entry["resolution_id"]])
        assert resolution["found"], name
        assert resolution["resolution"]["verdict"] == entry["observed_verdict"], name
        assert resolution["resolution"]["reason_code"] == entry["observed_reason"], name
        assert resolution["resolution"]["criteria"] == entry["criteria"], name
        checked += 1
    assert checked > 0


@pytest.mark.skipif(not TRANSCRIPT.exists(), reason="no live run recorded yet")
def test_the_monitor_view_agrees_with_the_full_verdict(client, record):
    checked = 0
    for name, entry in sorted(steps().items()):
        if not name.startswith("resolve:") or "submission_id" not in entry:
            continue
        sid = entry["submission_id"]
        full = read(client, record, "get_verdict", [sid])
        monitor = read(client, record, "is_policy_violation_confirmed", [sid])
        assert monitor["confirmed"] == (full["verdict"] == "POLICY_VIOLATION_CONFIRMED"), name
        assert monitor["final"] == full["final"], name
        assert full["policy_compliant"] == {"POLICY_COMPLIANT": True,
                                            "POLICY_VIOLATION_CONFIRMED": False}.get(
            full["verdict"]), name
        checked += 1
    assert checked > 0


@pytest.mark.skipif(not TRANSCRIPT.exists(), reason="no live run recorded yet")
def test_a_positive_verdict_never_rests_on_the_explanation_or_unbound_bytes(client, record):
    positives = [e for e in steps().values()
                 if e.get("observed_verdict") in ("POLICY_VIOLATION_CONFIRMED",
                                                  "POLICY_COMPLIANT")]
    assert positives
    for entry in positives:
        resolution = read(client, record, "get_resolution",
                          [entry["resolution_id"]])["resolution"]
        roles = {s["evidence_id"]: s for s in resolution["sources"]}
        for finding in resolution["findings"]:
            if finding["id"] not in ("VIOLATION_CONDITION", "DECISION_RULE",
                                     "PROHIBITED_FACTOR", "DECISION_RECORDED"):
                continue
            for quote in finding["quotes"]:
                assert roles[quote["evidence_id"]]["role"] != "EXPLANATION"
                assert roles[quote["evidence_id"]]["kind"] == "PINNED"
        # binding is a property of the case: every readable item that can be
        # evidence is pinned, whatever the readings quoted
        for source in resolution["sources"]:
            if source["role"] != "EXPLANATION" and source["status"] in ("RETRIEVED", "PARTIAL"):
                assert source["kind"] == "PINNED", source["evidence_id"]


@pytest.mark.skipif(not TRANSCRIPT.exists(), reason="no live run recorded yet")
def test_unavailable_evidence_never_ended_a_case_early(client, record):
    checked = 0
    for name, entry in steps().items():
        if name.startswith("resolve:") and entry.get("observed_verdict") == "EVIDENCE_UNAVAILABLE":
            assert entry["status_after"] == "PENDING", name
            checked += 1
    assert checked > 0
    lapsed = [e for n, e in steps().items() if n.startswith("lapse:")
              and e.get("expected_verdict") == "EVIDENCE_UNAVAILABLE, final"]
    for entry in lapsed:
        verdict = read(client, record, "get_verdict", [entry["args"][0]])
        assert verdict["verdict"] == "EVIDENCE_UNAVAILABLE" and verdict["final"] is True


@pytest.mark.skipif(not TRANSCRIPT.exists(), reason="no live run recorded yet")
def test_criteria_nobody_compared_are_served_as_null(client, record):
    checked = 0
    for name, entry in steps().items():
        if not name.startswith("resolve:") or "resolution_id" not in entry:
            continue
        resolution = read(client, record, "get_resolution",
                          [entry["resolution_id"]])["resolution"]
        keys = {"DECISION_RECORDED": "decision_recorded",
                "VIOLATION_CONDITION": "violation_condition_met",
                "DECISION_RULE": "rule_followed",
                "PROHIBITED_FACTOR": "prohibited_factor_detected",
                "EXPLANATION": "explanation_supported"}
        for finding in resolution["findings"]:
            if finding["id"] in keys and not finding["compared"]:
                assert resolution["criteria"][keys[finding["id"]]] is None, name
                checked += 1
    assert checked > 0


@pytest.mark.skipif(not TRANSCRIPT.exists(), reason="no live run recorded yet")
def test_unavailable_evidence_never_became_a_verdict(client, record):
    for name, entry in steps().items():
        if name.startswith("resolve:") and entry.get("observed_reason") in (
                "EVIDENCE_DIGEST_MISMATCH", "POLICY_UNREADABLE",
                "REQUIRED_EVIDENCE_UNREADABLE", "SOURCE_ADDRESSES_ADJUDICATOR"):
            assert entry["panel_state"] == "SKIPPED", name
            assert entry["observed_verdict"] in ("EVIDENCE_UNAVAILABLE", "INCONCLUSIVE")


@pytest.mark.skipif(os.environ.get("DS_LIVE_WRITES") != "1",
                    reason="set DS_LIVE_WRITES=1 to send one transaction")
def test_a_challenge_can_still_be_published(record):
    import studionet_transport  # noqa: F401
    from genlayer_py import create_account, create_client
    from genlayer_py.chains import studionet
    from genlayer_py.types import TransactionStatus
    keys = json.loads((ROOT / ".data" / "demo_wallets.json").read_text(encoding="utf-8"))
    writer = create_client(chain=studionet, account=create_account(
        account_private_key=keys["keeper"]), endpoint=RPC)
    run = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))
    template = json.loads((ROOT / "fixtures" / "challenges.json")
                          .read_text(encoding="utf-8"))["credit-line"]
    deadline = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600))
    text = json.dumps(template, sort_keys=True) \
        .replace("{policy_url}", run["raw_base"] + "evidence/policy-2026-09.html") \
        .replace("{deadline}", deadline)
    before = read(writer, record, "get_stats")["challenges"]
    tx = writer.write_contract(address=record["contract_address"],
                               function_name="publish_challenge", args=[text])
    writer.wait_for_transaction_receipt(transaction_hash=tx,
                                        status=TransactionStatus.FINALIZED,
                                        interval=5000, retries=240)
    assert read(writer, record, "get_stats")["challenges"] == before + 1
