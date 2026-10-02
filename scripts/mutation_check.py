#!/usr/bin/env python3
"""Mutation kill check: prove the Direct Mode suite pins each load-bearing
guard, not merely that the code passes today.

For each mutation the repository is copied to a scratch directory with ONE
guard in the contract mechanically broken, and the whole Direct Mode suite
runs against the copy. A mutation is KILLED when the suite fails and SURVIVED
when it passes (an unpinned guard). The run starts with an accept-control:
the unmodified copy must pass, or every kill would be vacuous.

Anchors are code TEXT, never line numbers. An anchor that is not found
exactly once is reported as ANCHOR MISSING - the guard moved or was deleted,
which is its own finding.

Run:  python scripts/mutation_check.py              (full sweep)
      python scripts/mutation_check.py --anchors    (anchor check only)
      python scripts/mutation_check.py --only gate  (names containing "gate";
                                                     separate several with |)
      python scripts/mutation_check.py --jobs 3     (three scratch copies)
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = "contracts/decisionshield.py"


def off(condition: str) -> tuple:
    """(anchor, replacement) turning one `if` line into `if False:`."""
    head = condition[:len(condition) - len(condition.lstrip())]
    keyword = condition.lstrip().split(" ", 1)[0]
    return (condition + "\n", head + keyword + " False:\n")


def m(name: str, anchor: str, replacement: str = None) -> tuple:
    if replacement is None:
        anchor, replacement = off(anchor)
    return (name, anchor, replacement)


MUTATIONS = [
    # -- retrieval ------------------------------------------------------------------------
    m("a redirect is read as a retrieved document", "    if 300 <= code < 400:"),
    m("a 404 is a generic failure", "    if code in (404, 410):"),
    m("a forbidden document is a generic failure", "    if code in (401, 403):"),
    m("a binary content type is read",
      '    if content_type != "" and not any(t in content_type for t in TEXT_TYPES):'),
    m("an undecodable body is read",
      '    if text is None:\n        return (_empty_source(INVALID_CONTENT',
      '    if False:\n        return (_empty_source(INVALID_CONTENT'),
    m("an oversized document is not marked partial",
      "    truncated = len(body) > BODY_BYTES_CAP or len(normalized) > TEXT_CAP\n",
      "    truncated = False\n"),
    # -- evidence integrity ---------------------------------------------------------------
    m("a pinned item's bytes are not checked against the declared digest",
      '                and source["raw_sha256"] != item["sha256"]:',
      '                and False:'),
    m("a digest mismatch is judged by the panel anyway",
      '    if any(s["status"] == DIGEST_MISMATCH for s in sources):'),
    m("an unreadable policy is judged anyway", '    if "P" not in readable:'),
    m("a required role that cannot be read is judged anyway",
      "        if not any(_role_of(ctx, e) == role for e in readable):"),
    m("a document addressing the adjudicator is judged anyway",
      "    if len(markers) > 0:\n        return \"SOURCE_ADDRESSES_ADJUDICATOR\"\n",
      "    if False:\n        return \"SOURCE_ADDRESSES_ADJUDICATOR\"\n"),
    m("text in the visible body is not scanned", "    if body_hit:"),
    m("markup and attributes are not scanned",
      "    if not body_hit and _evaluator_hits(_scan_form(raw_text)):"),
    m("the title is not scanned", '    if _evaluator_hits(_scan_form(source["title"])):'),
    # -- an explanation is a claim, never evidence ----------------------------------------
    m("a finding may be quoted from the explanation",
      '        return [e for e in eligible if _role_of(ctx, e) != ROLE_EXPLANATION]\n',
      "        return eligible\n"),
    m("a false explanation counts as contradictory evidence",
      "    if (subject_id in FINDING_SUBJECTS or subject_id == SUBJECT_CONSISTENCY) \\\n",
      "    if subject_id in FINDING_SUBJECTS \\\n"),
    m("the decision may be read from any item",
      '        return [e for e in eligible if _role_of(ctx, e) == ROLE_OUTPUT]\n',
      "        return eligible\n"),
    m("the gate lets a reading quote any item",
      '    quotable = _quotable(ctx, subject_id, f["state"], eligible)\n',
      "    quotable = eligible\n"),
    # -- what a reading must show ----------------------------------------------------------
    m("an assertion about the case needs no quote",
      "    return state in QUOTED[subject_id]\n", "    return False\n"),
    m("a spliced quote is accepted when the panel answers",
      '        if _spliced(rq["text"]):\n            continue\n', ""),
    m("a spliced quote passes the gate",
      '        if q in seen or _spliced(q["text"]) or not _quote_grounded(q, quotable, texts):',
      "        if q in seen or not _quote_grounded(q, quotable, texts):"),
    m("a quote need not ground in the text this node retrieved",
      "    return _grounds_in_order(_word_tokens(source), quote[\"text\"])\n",
      "    return True\n"),
    m("prohibited factors are asked about when none are declared",
      '    if len(ctx["challenge"]["prohibited_factors"]) > 0:\n'
      "        out.append(SUBJECT_FACTOR)\n",
      "    out.append(SUBJECT_FACTOR)\n"),
    # -- the verdict ----------------------------------------------------------------------
    m("a code reason about evidence is not EVIDENCE_UNAVAILABLE",
      '    if reason in ("EVIDENCE_DIGEST_MISMATCH", "POLICY_UNREADABLE",\n'
      '                  "REQUIRED_EVIDENCE_UNREADABLE"):\n'
      "        return (EVIDENCE_UNAVAILABLE, reason)\n",
      '    if False:\n        return (EVIDENCE_UNAVAILABLE, reason)\n'),
    m("a code reason is overridden by the panel's reading",
      '    if reason != "":\n        return (INCONCLUSIVE, reason)\n',
      '    if False:\n        return (INCONCLUSIVE, reason)\n'),
    m("an unusable panel answer reaches a verdict",
      '    if payload["panel_state"] != PANEL_ASSESSED:\n'
      '        return (INCONCLUSIVE, "PANEL_UNUSABLE")',
      '    if False:\n        return (INCONCLUSIVE, "PANEL_UNUSABLE")'),
    m("contradictory evidence reaches a verdict", "    if consistency == CONTRADICTORY:"),
    m("unclear consistency reaches a verdict", "    if consistency == UNCLEAR:"),
    m("a decision the output does not record is judged anyway", "    if decision == DIFFERS:"),
    m("an unclear decision is judged anyway", "    if decision == UNCLEAR:"),
    m("a violation needs no bound bytes",
      "        if not _bound(ctx, payload, [SUBJECT_DECISION, SUBJECT_VIOLATION]):"),
    m("an unclear violation falls through to compliance", "    if violation == UNCLEAR:"),
    m("a broken rule beside an unmet violation is compliance",
      "    if rule == BROKEN or factor == USED or explanation == CONTRADICTED:"),
    m("a prohibited factor beside an unmet violation is compliance",
      "    if rule == BROKEN or factor == USED or explanation == CONTRADICTED:",
      "    if rule == BROKEN or explanation == CONTRADICTED:"),
    m("a contradicted explanation beside an unmet violation is compliance",
      "    if rule == BROKEN or factor == USED or explanation == CONTRADICTED:",
      "    if rule == BROKEN or factor == USED:"),
    m("an unclear criterion is compliance", "    if UNCLEAR in (rule, factor, explanation):"),
    m("compliance needs no bound bytes",
      "    if not _bound(ctx, payload, [SUBJECT_DECISION, SUBJECT_RULE]):"),
    m("a live item counts as bound",
      '            if item is None or item["kind"] != KIND_PINNED:\n'
      "                return False\n",
      "            if item is None:\n                return False\n"),
    m("the severity is not the challenge's",
      '    severity = ctx["challenge"]["severity"] if verdict == VIOLATION_CONFIRMED else ""\n',
      '    severity = "" if verdict == VIOLATION_CONFIRMED else ""\n'),
    # -- what validators compare -----------------------------------------------------------
    m("the consequence is not compared",
      "    for key in sorted(mine.keys()):\n        if mine[key] != theirs[key]:\n",
      "    for key in sorted(mine.keys()):\n        if False:\n"),
    m("a positive verdict's criteria are not compared",
      '        "criteria": criteria if verdict in POSITIVE_VERDICTS else {},\n',
      '        "criteria": {},\n'),
    m("the leader's payload is gated against its own text, not this node's",
      "        parsed = _parse_payload(leader_res.calldata, ctx, own_texts)\n",
      "        parsed = _parse_payload(leader_res.calldata, ctx, None)\n"),
    m("a transient failure ratifies a different failure",
      "        if leader_text.startswith(ERROR_TRANSIENT):\n"
      "            return own_text.startswith(ERROR_TRANSIENT)\n"
      "        return own_text == leader_text\n",
      "        return True\n"),
    m("a payload about another case is accepted",
      '            or p["submission_id"] != ctx["submission_id"] or not _is_int(p["round"]) \\\n',
      '            or not _is_int(p["round"]) \\\n'),
    # -- the challenge ---------------------------------------------------------------------
    m("the policy may come from any host",
      '    if not _domain_allowed(_host_of(canonical), domains):\n'
      '        return ("policy_url is outside',
      '    if False:\n        return ("policy_url is outside'),
    m("the policy need not be bound", '    if not _is_hex(spec["policy_sha256"], 64):'),
    m("the model output need not be required", "    if ROLE_OUTPUT not in required:"),
    m("prohibited factors may repeat", "        if key in seen:"),
    m("the severity may be anything", '    if spec["severity"] not in SEVERITIES:'),
    m("the windows are unbounded", "        if not _int_in(spec[field], MIN_WINDOW, MAX_WINDOW):"),
    m("a challenge may close in the past",
      '        if _iso_epoch(now) >= _iso_epoch(spec["submission_deadline"]):'),
    m("challenge text may address the adjudicator",
      "    if _evaluator_hits(value) or _hidden_hits(value):"),
    m("an IP literal is a host", "    if all_numeric or labels[-1].isdigit():"),
    # -- privacy ---------------------------------------------------------------------------
    m("an email address passes the privacy guard",
      '    if re.search("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}", value):'),
    m("a long digit run passes the privacy guard", "        if run >= DIGIT_RUN_LIMIT:"),
    m("a space continues a digit run",
      '        run = run + 1 if ch.isdigit() else (run if ch == "-" and run > 0 else 0)\n',
      '        run = run + 1 if ch.isdigit() else (run if ch in " -" and run > 0 else 0)\n'),
    m("free text skips the privacy guard",
      "    return _privacy_error(value, label)\n", '    return ""\n'),
    # -- the evidence a case declares ------------------------------------------------------
    m("a pinned item needs no digest", '            if not _is_hex(entry["sha256"], 64):'),
    m("a live item may declare a digest it is not held to", '        elif entry["sha256"] != "":'),
    m("an item may claim the policy role", '        if entry["role"] not in SUBMITTED_ROLES:'),
    m("an item may come from any host",
      '        if not _domain_allowed(_host_of(canonical_url), spec["evidence_domains"]):'),
    m("the same document may be declared twice", "        if canonical_url in urls:"),
    m("a required role may be missing at filing",
      '        if not any(entry["role"] == role for entry in values):'),
    m("the evidence list is unbounded",
      "    if not isinstance(values, list) or len(values) < 1 or len(values) > MAX_EVIDENCE:"),
    # -- the state machine -----------------------------------------------------------------
    m("a stale policy version is accepted",
      '        if policy_version != spec["policy_version"]:'),
    m("a policy hash mismatch is accepted", '        if policy_sha256 != spec["policy_sha256"]:'),
    m("the challenge hash is not checked",
      "        if challenge_hash != str(challenge.definition_hash):"),
    m("a case may be filed after the deadline", "        if status == CH_CLOSED:"),
    m("a case may be filed against a cancelled challenge", "        if status == CH_CANCELLED:"),
    m("the claimed violation may be anything",
      "        if claimed_violation not in CLAIMED_VIOLATIONS:"),
    m("one tester may file twice", "        if held is not None:"),
    m("the open-case cap does not hold",
      "        if self._counter_value(wallet) >= MAX_OPEN_PER_WALLET:"),
    m("a case may be resolved twice",
      '        if str(submission.status) != SUB_PENDING:\n'
      '            self._fail("only a PENDING case is resolved")',
      '        if False:\n            self._fail("only a PENDING case is resolved")'),
    m("a case may be resolved after its window",
      '        if _iso_epoch(now) > _iso_epoch(str(submission.window_ends)):\n'
      '            self._fail("the resolve window closed at "',
      '        if False:\n            self._fail("the resolve window closed at "'),
    m("a verdict may be contested twice", "        if bool(submission.contested):"),
    m("a stranger may contest",
      "        if self._sender_hex() not in (str(submission.tester), "
      "str(challenge.publisher)):"),
    m("a verdict may be contested after its window",
      '        if _iso_epoch(now) > _iso_epoch(str(submission.window_ends)):\n'
      '            self._fail("the contest window closed at "',
      '        if False:\n            self._fail("the contest window closed at "'),
    m("a verdict may be final inside its contest window",
      '        if _iso_epoch(now) <= _iso_epoch(str(submission.window_ends)):\n'
      '            self._fail("the contest window closes at "',
      '        if False:\n            self._fail("the contest window closes at "'),
    m("a case may lapse while its window is open",
      '        if _iso_epoch(now) <= _iso_epoch(str(submission.window_ends)):\n'
      '            self._fail("the resolve window closes at "',
      '        if False:\n            self._fail("the resolve window closes at "'),
    m("anyone may withdraw a case", "        if self._sender_hex() != str(submission.tester):"),
    m("a challenge with cases may be cancelled", "        if len(challenge.submission_ids) > 0:"),
    m("anyone may cancel a challenge",
      "        if self._sender_hex() != str(challenge.publisher):"),
    m("a record stores a live item's bytes",
      '            pinned = item is not None and item["kind"] == KIND_PINNED\n',
      "            pinned = True\n"),
    m("every reading is marked compared",
      '            entry["compared"] = self._compared(ctx, outcome, finding)\n',
      '            entry["compared"] = True\n'),
    m("the violation count is not corrected when a contest overturns",
      "        if was and not is_now:\n"
      "            self.violation_counter = u32(int(self.violation_counter) - 1)\n", ""),
]


def run_suite(workdir: pathlib.Path) -> bool:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/direct", "-q", "-x", "-p", "no:cacheprovider",
         "--no-header"], cwd=workdir, capture_output=True, text=True)
    return completed.returncode == 0


def check_anchors(source: str) -> int:
    missing = 0
    for name, old, _new in MUTATIONS:
        hits = source.count(old)
        if hits != 1:
            print(f"ANCHOR MISSING ({hits} hits): {name}")
            missing += 1
    return missing


def copy_repo(scratch: pathlib.Path, index: int) -> pathlib.Path:
    work = scratch / ("repo%d" % index)
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", ".pytest_cache", "deploy", "artifacts", ".data", "docs"))
    return work


def main() -> None:
    source = (ROOT / CONTRACT).read_text(encoding="utf-8")
    missing = check_anchors(source)
    print(f"{len(MUTATIONS)} mutations, {missing} anchor problems")
    if "--anchors" in sys.argv:
        sys.exit(0 if missing == 0 else 1)
    only = ""
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].casefold()
    jobs = 1
    if "--jobs" in sys.argv:
        jobs = max(1, int(sys.argv[sys.argv.index("--jobs") + 1]))
    todo = [x for x in MUTATIONS if source.count(x[1]) == 1
            and (not only or any(part in x[0].casefold() for part in only.split("|")))]
    jobs = min(jobs, max(1, len(todo)))
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="ds-mut-"))
    copies = [copy_repo(scratch, i) for i in range(jobs)]
    print("accept-control: unmodified copy must pass ...", flush=True)
    if not run_suite(copies[0]):
        print("CONTROL FAILED: the unmodified suite does not pass; aborting")
        shutil.rmtree(scratch, ignore_errors=True)
        sys.exit(1)
    print(f"control green; {len(todo)} mutations over {jobs} job(s)\n", flush=True)
    results = [None] * len(todo)
    cursor = [0]
    done = [0]
    lock = threading.Lock()

    def worker(work: pathlib.Path) -> None:
        target = work / CONTRACT
        while True:
            with lock:
                i = cursor[0]
                if i >= len(todo):
                    return
                cursor[0] = i + 1
            name, old, new = todo[i]
            target.write_text(source.replace(old, new), encoding="utf-8", newline="\n")
            passed = run_suite(work)
            target.write_text(source, encoding="utf-8", newline="\n")
            with lock:
                results[i] = passed
                done[0] += 1
                print(f"  [{done[0]}/{len(todo)}] {'SURVIVED' if passed else 'killed  '}: "
                      f"{name}", flush=True)

    threads = [threading.Thread(target=worker, args=(w,)) for w in copies]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    shutil.rmtree(scratch, ignore_errors=True)
    print()
    killed = survived = 0
    for (name, _old, _new), passed in zip(todo, results):
        print(("SURVIVED: " if passed else "killed:   ") + name)
        survived += 1 if passed else 0
        killed += 0 if passed else 1
    print(f"\nmutations: {killed} killed, {survived} survived, {missing} anchor missing")
    sys.exit(0 if survived == 0 and missing == 0 else 1)


if __name__ == "__main__":
    main()
