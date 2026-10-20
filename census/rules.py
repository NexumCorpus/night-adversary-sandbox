"""Fixed rules of the false-green census, shared by collect.py and verify.py.

Standard library only. The regexes are read from the fenced blocks in PREREG.md, so the code
cannot drift from the pre-registration. Everything else here implements PREREG.md word for word.
"""

import hashlib
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.join(HERE, "PREREG.md")

AGENTS = ["codex", "devin", "copilot", "cursor", "claude_code"]
AGENT_NAMES = {
    "codex": "OpenAI Codex",
    "devin": "Devin",
    "copilot": "GitHub Copilot coding agent",
    "cursor": "Cursor",
    "claude_code": "Claude Code",
}
FIELDS = [
    "row_id", "agent", "repo", "pr_number", "pr_url", "pr_state", "merged", "author_type",
    "pr_created_at", "pr_closed_at", "body_last_edited_at", "edit_info", "head_sha", "head_committed_at",
    "claim_rule", "claim_snippet", "n_claim_lines", "ci", "ci_core", "n_checks", "ci_last_completed_at",
    "claim_aligned", "checks_json", "frame", "collected_at", "hand_label", "hand_note",
]
TARGET_PER_AGENT = 75
MAX_FETCH_PER_AGENT = 1500
REPO_CAP = 2
MIN_N = 30
KILL_UPPER = 0.05
HAND_N = 30
SNIPPET_MAX = 200
Z95 = 1.959964


def _load_blocks(path=PREREG):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = {}
    for name, body in re.findall(r"^```([a-z-]+)\n(.*?)^```", text, re.M | re.S):
        rules = []
        for line in body.splitlines():
            if not line.strip():
                continue
            rule_id, pattern = line.split(None, 1)
            rules.append((rule_id, re.compile(pattern, re.IGNORECASE)))
        blocks[name] = rules
    return blocks


BLOCKS = _load_blocks()
CLAIM_RULES = BLOCKS["claim-rules"]
OBJECT_GUARD = BLOCKS["object-guard"]
NEUTRALIZE = BLOCKS["guard-neutralize"]
GUARDS = BLOCKS["guard-rules"]
CHECKED_BOX = BLOCKS["checked-box"]
NON_TEST = BLOCKS["non-test-checks"]

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_QUOTED_TASK = re.compile(
    r"<details[^>]*>\s*<summary[^>]*>(?:(?!</summary>).)*?(?:prompt|original|issue)"
    r"(?:(?!</summary>).)*?</summary>.*?</details>",
    re.S | re.I,
)
_TAG = re.compile(r"<[^>\n]+>")
_MENTION = re.compile(r"@[A-Za-z0-9][A-Za-z0-9-]*")


def agent_of(label):
    """Map an AIDev agent label to a census agent id (None if not one of the five)."""
    low = (label or "").lower()
    for key, agent in (("codex", "codex"), ("devin", "devin"), ("copilot", "copilot"),
                       ("cursor", "cursor"), ("claude", "claude_code")):
        if key in low:
            return agent
    return None


def normalized_lines(title, body):
    text = (title or "") + "\n" + (body or "")
    text = _COMMENT.sub(" ", text)
    text = _QUOTED_TASK.sub(" ", text)
    out = []
    for raw in text.replace("\r", "").split("\n"):
        if raw.lstrip().startswith(">"):
            continue
        line = _TAG.sub(" ", raw).replace("*", "").replace("`", "")
        line = " ".join(line.split())
        if line:
            out.append(line)
    return out


def claim_match(line):
    """Return (rule_id, match) if the normalised line is a claim line, else None."""
    hit = None
    for rule_id, rx in CLAIM_RULES:
        for m in rx.finditer(line):
            if not any(g.match(line[m.end():]) for _, g in OBJECT_GUARD):
                hit = (rule_id, m)
                break
        if hit:
            break
    if not hit:
        return None
    probe = line
    for _, rx in NEUTRALIZE:
        probe = rx.sub(" ", probe)
    checked = any(rx.search(line) for _, rx in CHECKED_BOX)
    for rule_id, rx in GUARDS:
        if rule_id == "G4" and checked:
            continue
        if rx.search(probe):
            return None
    return hit


def snippet_of(line, m):
    line = _MENTION.sub("@user", line)
    # Masking can shift positions; find the match again in the masked line.
    m2 = re.search(re.escape(m.group(0)), line) or m
    start = 0 if m2.start() < 140 else m2.start() - 60
    return line[start:start + SNIPPET_MAX]


def find_claim(title, body):
    """Return dict(rule, snippet, n_lines) for the first claim line, or None."""
    first = None
    count = 0
    for line in normalized_lines(title, body):
        hit = claim_match(line)
        if hit:
            count += 1
            if first is None:
                first = (hit[0], snippet_of(line, hit[1]))
    if first is None:
        return None
    return {"rule": first[0], "snippet": first[1], "n_lines": count}


# --- CI mapping -----------------------------------------------------------------------------

RUN_FAILURE = {"failure", "timed_out", "startup_failure"}


def item_state(item):
    """item = [kind, app, name, status_or_state, conclusion, timestamp] as stored in checks_json."""
    kind, _app, _name, raw, conclusion = item[:5]
    if kind == "run":
        if raw != "completed":
            return "pending"
        if conclusion == "success":
            return "success"
        if conclusion in RUN_FAILURE:
            return "failure"
        return "neutral"
    if raw == "success":
        return "success"
    if raw in ("failure", "error"):
        return "failure"
    if raw == "pending":
        return "pending"
    return "neutral"


def is_non_test(item):
    kind, app, name = item[:3]
    label = (app + " " + name) if kind == "run" else name
    return any(rx.search(label) for _, rx in NON_TEST)


def rollup(items):
    states = {item_state(i) for i in items}
    for s in ("failure", "pending", "success"):
        if s in states:
            return s
    return "none"


def ci_of(items):
    return rollup(items), rollup([i for i in items if not is_non_test(i)])


def checks_json(items):
    return json.dumps(items, ensure_ascii=False, separators=(",", ":"))


# --- statistics and ordering ----------------------------------------------------------------

def wilson(k, n, z=Z95):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def frame_key(agent, repo, number):
    return _sha(f"census-a:{agent}:{repo}#{number}".lower())


def hand_key(row_id):
    return _sha(f"precision-30:{row_id}")
