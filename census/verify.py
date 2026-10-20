#!/usr/bin/env python3
"""Recompute every number in results.md from data.csv. Standard library only.

    python3 census/verify.py               check data.csv and results.md; exit 1 on any mismatch
    python3 census/verify.py --write       rewrite the computed block in results.md
    python3 census/verify.py --hand-sample list the rows chosen for the hand check of claim precision

Every number in results.md outside the computed block must be a pre-registered constant
(see CONSTANTS); everything else lives in the computed block, which this script writes.
"""

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.csv")
RESULTS = os.path.join(HERE, "results.md")
BEGIN = "<!-- verify.py:begin (generated from data.csv; do not edit by hand) -->"
END = "<!-- verify.py:end -->"
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
LIST_MARKER = re.compile(r"^\s*\d+\.\s", re.M)
CODE = re.compile(r"`[^`\n]*`")
CONSTANTS = {"95%", "5%", "30", "75", "200", "2", "1,500", "80%"}
DETERMINATE = ("success", "failure")


def load(path=DATA):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != rules.FIELDS:
            raise SystemExit(f"data.csv header differs from rules.FIELDS: {reader.fieldnames}")
        return list(reader)


def check_rows(rows):
    """Re-derive what can be re-derived. Returns (errors, warnings)."""
    errors, warnings, seen, per_repo = [], [], set(), {}
    claim_rx = dict(rules.CLAIM_RULES)
    for r in rows:
        rid = r["row_id"]
        if rid in seen:
            errors.append(f"{rid}: duplicate row_id")
        seen.add(rid)
        if r["agent"] not in rules.AGENTS:
            errors.append(f"{rid}: unknown agent {r['agent']}")
        if not (rid.startswith(r["agent"] + ":") and rid.endswith("#" + r["pr_number"])):
            errors.append(f"{rid}: row_id does not match agent/pr_number")
        key = (r["agent"], r["repo"].lower())
        per_repo[key] = per_repo.get(key, 0) + 1
        items = json.loads(r["checks_json"])
        if [r["ci"], r["ci_core"]] != list(rules.ci_of(items)):
            errors.append(f"{rid}: ci/ci_core {r['ci']}/{r['ci_core']} != re-derived {rules.ci_of(items)}")
        if int(r["n_checks"]) != len(items):
            errors.append(f"{rid}: n_checks {r['n_checks']} != {len(items)}")
        snip = r["claim_snippet"]
        if len(snip) > rules.SNIPPET_MAX:
            errors.append(f"{rid}: snippet longer than {rules.SNIPPET_MAX}")
        if r["claim_rule"] not in claim_rx or not claim_rx[r["claim_rule"]].search(snip):
            errors.append(f"{rid}: rule {r['claim_rule']} does not match the snippet")
        elif rules.claim_match(snip) is None:
            warnings.append(f"{rid}: snippet alone fails a guard (line was cut to {rules.SNIPPET_MAX} chars)")
        if r["edit_info"] == "graphql" and r["head_committed_at"]:
            claim_time = r["body_last_edited_at"] or r["pr_created_at"]
            want = "1" if claim_time >= r["head_committed_at"] else "0"
            if r["claim_aligned"] != want:
                errors.append(f"{rid}: claim_aligned {r['claim_aligned']} != {want}")
        elif r["claim_aligned"]:
            errors.append(f"{rid}: claim_aligned set without GraphQL edit time and commit date")
        if r["hand_label"] not in ("", "claim", "not_claim"):
            errors.append(f"{rid}: hand_label must be claim, not_claim or empty")
    for (agent, repo), count in per_repo.items():
        if count > rules.REPO_CAP:
            errors.append(f"{agent} {repo}: {count} rows, cap is {rules.REPO_CAP}")
    labelled = {r["row_id"] for r in rows if r["hand_label"]}
    chosen = set(hand_sample(rows))
    if labelled - chosen:
        errors.append(f"hand labels on rows outside the pre-registered sample: {sorted(labelled - chosen)}")
    return errors, warnings


def hand_sample(rows):
    return sorted((r["row_id"] for r in rows), key=rules.hand_key)[:rules.HAND_N]


def pct(x):
    return f"{100 * x:.1f}%"


def rate_cells(k, n):
    if n < rules.MIN_N:
        return [f"not reported (n < {rules.MIN_N})", ""]
    lo, hi = rules.wilson(k, n)
    return [pct(k / n), f"{pct(lo)} to {pct(hi)}"]


def table(header, body):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return out


def count(rows, field, value):
    return sum(1 for r in rows if r[field] == value)


def render(rows):
    lines = [BEGIN, ""]
    by_agent = {a: [r for r in rows if r["agent"] == a] for a in rules.AGENTS}
    n_all = sum(1 for r in rows if r["ci"] in DETERMINATE)
    if not rows:
        lines += ["data.csv has 0 rows. There is nothing to report yet.", "", END]
        return "\n".join(lines)
    frames = sorted({r["frame"] for r in rows})
    stamps = sorted(r["collected_at"] for r in rows)
    lines += [f"data.csv: {len(rows)} claim PRs, {n_all} of them with CI success or failure. "
              f"Frame: {', '.join(frames)}. Collected {stamps[0]} to {stamps[-1]}.", ""]

    # Primary
    body, evaluable = [], {}
    for a in rules.AGENTS + ["all"]:
        rs = rows if a == "all" else by_agent[a]
        s, f = count(rs, "ci", "success"), count(rs, "ci", "failure")
        n = s + f
        name = "All agents (unweighted)" if a == "all" else rules.AGENT_NAMES[a]
        body.append([name, len(rs), s, f, count(rs, "ci", "none"), count(rs, "ci", "pending"), n, f]
                    + rate_cells(f, n))
        if a != "all" and n >= rules.MIN_N:
            evaluable[a] = rules.wilson(f, n)[1]
    lines += ["### Primary: CI at the head SHA", ""]
    lines += table(["Agent", "Claim PRs", "CI success", "CI failure", "CI none", "CI pending", "n",
                    "False greens", "Rate", "Wilson 95% CI"], body)
    lines += ["", "n = CI success + CI failure. The unweighted row pools the sample; it is not an estimate "
              "for all agent PRs.", ""]

    # Secondary: core CI
    body = []
    for a in rules.AGENTS:
        rs = by_agent[a]
        f = count(rs, "ci_core", "failure")
        n = f + count(rs, "ci_core", "success")
        body.append([rules.AGENT_NAMES[a], n, f] + rate_cells(f, n))
    lines += ["### Secondary: core CI (checks that do not build or test the code removed)", ""]
    lines += table(["Agent", "n", "False greens", "Rate", "Wilson 95% CI"], body) + [""]

    # Secondary: aligned rows
    known = sum(1 for r in rows if r["claim_aligned"] in ("0", "1"))
    lines += ["### Secondary: claim text written at or after the head commit", "",
              f"Alignment is known for {known} of {len(rows)} rows ({pct(known / len(rows))})."]
    if known >= 0.8 * len(rows):
        body = []
        for a in rules.AGENTS:
            rs = [r for r in by_agent[a] if r["claim_aligned"] == "1"]
            f = count(rs, "ci", "failure")
            n = f + count(rs, "ci", "success")
            body.append([rules.AGENT_NAMES[a], n, f] + rate_cells(f, n))
        lines += [""] + table(["Agent", "n", "False greens", "Rate", "Wilson 95% CI"], body)
    else:
        lines += ["That is below the pre-registered 80%, so no aligned-only rates are reported."]
    lines += [""]

    # Kill condition
    lines += ["### Kill condition", ""]
    if len(evaluable) < 2:
        lines += [f"Inconclusive: {len(evaluable)} agent(s) reached n >= {rules.MIN_N}; "
                  "phase B is redesigned rather than run as planned."]
    elif all(hi < rules.KILL_UPPER for hi in evaluable.values()):
        lines += ["Met: the Wilson upper bound is below 5% for every agent with n >= 30. Phase B stops."]
    else:
        above = [rules.AGENT_NAMES[a] for a, hi in evaluable.items() if hi >= rules.KILL_UPPER]
        lines += [f"Not met: the Wilson upper bound is 5% or more for {', '.join(above)}. Phase B may proceed."]
    lines += [""]

    # Hand check
    sample = set(hand_sample(rows))
    labels = [r["hand_label"] for r in rows if r["row_id"] in sample and r["hand_label"]]
    lines += ["### Hand check of claim precision", ""]
    if len(labels) < len(sample):
        lines += [f"Pending: {len(labels)} of {len(sample)} sampled rows labelled."]
    else:
        k = labels.count("claim")
        lo, hi = rules.wilson(k, len(labels))
        lines += [f"{k} of {len(labels)} sampled snippets are real success claims: precision {pct(k / len(labels))} "
                  f"(Wilson 95% CI {pct(lo)} to {pct(hi)})."]
        bad = sorted(r["claim_rule"] for r in rows if r["row_id"] in sample and r["hand_label"] == "not_claim")
        if bad:
            lines += [f"Rules behind the {len(bad)} non-claims: {', '.join(bad)}."]
    lines += ["", END]
    return "\n".join(lines)


def split_results(text):
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise SystemExit("results.md must contain the computed block markers exactly once")
    head, rest = text.split(BEGIN, 1)
    block, tail = rest.split(END, 1)
    return head, BEGIN + block + END, tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--hand-sample", action="store_true")
    args = ap.parse_args()

    rows = load()
    if args.hand_sample:
        by_id = {r["row_id"]: r for r in rows}
        for rid in hand_sample(rows):
            r = by_id[rid]
            print(f"{rid}\t{r['hand_label'] or '-'}\t{r['claim_rule']}\t{r['pr_url']}\n    {r['claim_snippet']}")
        return 0

    errors, warnings = check_rows(rows)
    for w in warnings:
        print("warning:", w)
    block = render(rows)
    with open(RESULTS, encoding="utf-8") as f:
        text = f.read()
    head, old_block, tail = split_results(text)
    if args.write:
        with open(RESULTS, "w", encoding="utf-8") as f:
            f.write(head + block + tail)
        old_block = block
    if old_block != block:
        errors.append("results.md computed block differs from data.csv (run with --write and review the diff)")
    prose = LIST_MARKER.sub("", CODE.sub("", head + tail))
    stray = sorted(set(NUMBER.findall(prose)) - CONSTANTS)
    if stray:
        errors.append(f"numbers in results.md outside the computed block that are not pre-registered "
                      f"constants: {stray}")
    for e in errors:
        print("ERROR:", e)
    n_det = sum(1 for r in rows if r["ci"] in DETERMINATE)
    print(f"{len(rows)} rows, {n_det} with CI success/failure; {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
