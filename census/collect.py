#!/usr/bin/env python3
"""Collect phase A of the false-green census, exactly as PREREG.md describes. Read-only.

Usage:
    export GITHUB_TOKEN=...            # any token with public read access
    python3 census/collect.py --aidev all_pull_request.parquet
    python3 census/collect.py --probe owner/repo#123     # print one PR's claim and CI, write nothing

The AIDev table is read with pyarrow (pip install pyarrow); everything else is the standard library.
The run can be stopped and restarted: rows already in data.csv and the scan position in scan_log.json
are kept.
"""

import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import rules

API = "https://api.github.com"
HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = rules.FIELDS
COUNTERS = ["offline_no_claim", "fetched", "gone", "claim_removed", "repo_cap", "ci_unreadable",
            "recorded", "determinate"]


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class GitHub:
    def __init__(self, token):
        self.token = token
        self.graphql_ok = True

    def _request(self, url, data=None):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "false-green-census/phase-a",
            "Authorization": "Bearer " + self.token,
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data).encode()
        for attempt in range(6):
            req = urllib.request.Request(url, data=data, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    body = json.loads(resp.read().decode() or "null")
                    self._pace(resp.headers)
                    return resp.status, body
            except urllib.error.HTTPError as e:
                text = e.read().decode(errors="replace")
                if e.code in (403, 429) and self._rate_limited(e.headers, text):
                    continue
                if e.code >= 500 and attempt < 5:
                    time.sleep(2 ** (attempt + 1))
                    continue
                try:
                    return e.code, json.loads(text)
                except ValueError:
                    return e.code, {"message": text[:200]}
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == 5:
                    raise
                time.sleep(2 ** (attempt + 1))
        raise RuntimeError("giving up on " + url)

    def _pace(self, headers):
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        if remaining is not None and reset and int(remaining) < 20:
            wait = max(0, int(reset) - time.time()) + 2
            print(f"  rate limit low ({remaining}); sleeping {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)

    def _rate_limited(self, headers, text):
        if headers.get("Retry-After"):
            time.sleep(int(headers["Retry-After"]) + 1)
            return True
        if headers.get("X-RateLimit-Remaining") == "0" and headers.get("X-RateLimit-Reset"):
            time.sleep(max(0, int(headers["X-RateLimit-Reset"]) - time.time()) + 2)
            return True
        if "secondary rate limit" in text.lower():
            time.sleep(60)
            return True
        return False

    def get(self, path, **params):
        url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
        return self._request(url)

    def pages(self, path, key, max_pages, **params):
        items, total = [], None
        for page in range(1, max_pages + 1):
            status, body = self.get(path, per_page=100, page=page, **params)
            if status != 200:
                return items, status
            batch = body.get(key) or []
            total = body.get("total_count", total)
            items.extend(batch)
            if len(batch) < 100 or (total is not None and len(items) >= total):
                break
        return items, 200

    def last_edited(self, repo, number):
        """Return (lastEditedAt or '', createdAt) via GraphQL, or None if GraphQL is unavailable."""
        if not self.graphql_ok:
            return None
        owner, name = repo.split("/", 1)
        query = ("query($o:String!,$n:String!,$k:Int!){repository(owner:$o,name:$n)"
                 "{pullRequest(number:$k){lastEditedAt createdAt}}}")
        status, body = self._request(API + "/graphql",
                                     {"query": query, "variables": {"o": owner, "n": name, "k": number}})
        pr = ((body or {}).get("data") or {}).get("repository") or {}
        pr = pr.get("pullRequest") if isinstance(pr, dict) else None
        if status != 200 or not pr:
            if status in (401, 403):
                self.graphql_ok = False
            return None
        return pr.get("lastEditedAt") or "", pr["createdAt"]


class CiUnreadable(Exception):
    pass


def ci_items(gh, repo, sha):
    runs, s1 = gh.pages(f"/repos/{repo}/commits/{sha}/check-runs", "check_runs", 10, filter="latest")
    statuses, s2 = gh.pages(f"/repos/{repo}/commits/{sha}/status", "statuses", 5)
    if s1 != 200 or s2 != 200:
        raise CiUnreadable(f"CI read failed for {repo}@{sha}: {s1}/{s2}")
    items = [["run", ((r.get("app") or {}).get("slug") or ""), r.get("name") or "", r.get("status") or "",
              r.get("conclusion") or "", r.get("completed_at") or ""] for r in runs]
    items += [["status", "", s.get("context") or "", s.get("state") or "", "", s.get("updated_at") or ""]
              for s in statuses]
    return items


def record_pr(gh, agent, row_id, pr, claim, frame_tag):
    repo = pr["base"]["repo"]["full_name"]
    sha = pr["head"]["sha"]
    items = ci_items(gh, repo, sha)
    ci, ci_core = rules.ci_of(items)
    status, commit = gh.get(f"/repos/{repo}/commits/{sha}")
    committed = ""
    if status == 200:
        committed = ((commit.get("commit") or {}).get("committer") or {}).get("date") or ""
    edited = gh.last_edited(repo, pr["number"])
    if edited is None:
        last_edit, edit_info, aligned = "", "unavailable", ""
    else:
        last_edit, edit_info = edited[0], "graphql"
        claim_time = edited[0] or edited[1]
        aligned = "" if not committed else ("1" if claim_time >= committed else "0")
    done = [i[5] for i in items if i[5]]
    return {
        "row_id": row_id, "agent": agent, "repo": repo, "pr_number": pr["number"], "pr_url": pr["html_url"],
        "pr_state": pr["state"], "merged": "1" if pr.get("merged_at") else "0",
        "author_type": (pr.get("user") or {}).get("type", ""),
        "pr_created_at": pr.get("created_at") or "", "pr_closed_at": pr.get("closed_at") or "",
        "body_last_edited_at": last_edit, "edit_info": edit_info, "head_sha": sha, "head_committed_at": committed,
        "claim_rule": claim["rule"], "claim_snippet": claim["snippet"], "n_claim_lines": claim["n_lines"],
        "ci": ci, "ci_core": ci_core, "n_checks": len(items), "ci_last_completed_at": max(done) if done else "",
        "claim_aligned": aligned, "checks_json": rules.checks_json(items), "frame": frame_tag,
        "collected_at": now(), "hand_label": "", "hand_note": "",
    }


def load_frame(path):
    import pyarrow.parquet as pq

    names = pq.ParquetFile(path).schema_arrow.names
    wanted = [c for c in ("agent", "title", "body", "html_url", "repo_url", "number") if c in names]
    if "agent" not in wanted or "body" not in wanted or not ({"html_url"} <= set(wanted)
                                                             or {"repo_url", "number"} <= set(wanted)):
        sys.exit(f"unexpected AIDev columns: {names}")
    table = pq.read_table(path, columns=wanted)
    cols = {c: table.column(c) for c in wanted}
    frame = {a: [] for a in rules.AGENTS}
    agents = cols["agent"].to_pylist()
    urls = cols["html_url"].to_pylist() if "html_url" in cols else [None] * len(agents)
    repo_urls = cols["repo_url"].to_pylist() if "repo_url" in cols else [None] * len(agents)
    numbers = cols["number"].to_pylist() if "number" in cols else [None] * len(agents)
    for i, label in enumerate(agents):
        agent = rules.agent_of(label)
        if agent is None:
            continue
        m = re.search(r"github\.com/([^/]+/[^/]+)/pull/(\d+)", urls[i] or "")
        if m:
            repo, number = m.group(1), int(m.group(2))
        else:
            m = re.search(r"repos/([^/]+/[^/]+?)/?$", repo_urls[i] or "")
            if not m or numbers[i] is None:
                continue
            repo, number = m.group(1), int(numbers[i])
        frame[agent].append((rules.frame_key(agent, repo, number), i, repo, number))
    for rows in frame.values():
        rows.sort()

    def text(i):
        title = cols["title"][i].as_py() if "title" in cols else ""
        return title, cols["body"][i].as_py()

    return frame, text


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def probe(gh, spec):
    m = re.fullmatch(r"([^/#\s]+/[^/#\s]+)#(\d+)", spec)
    if not m:
        sys.exit("--probe expects owner/repo#number")
    status, pr = gh.get(f"/repos/{m.group(1)}/pulls/{m.group(2)}")
    if status != 200:
        sys.exit(f"PR fetch failed: {status} {pr.get('message', '')}")
    claim = rules.find_claim(pr.get("title"), pr.get("body"))
    items = ci_items(gh, pr["base"]["repo"]["full_name"], pr["head"]["sha"])
    print(json.dumps({"claim": claim, "head_sha": pr["head"]["sha"], "ci": rules.ci_of(items),
                      "items": [i + [rules.item_state(i), rules.is_non_test(i)] for i in items]}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aidev", help="path to AIDev all_pull_request.parquet")
    ap.add_argument("--out", default=os.path.join(HERE, "data.csv"))
    ap.add_argument("--log", default=os.path.join(HERE, "scan_log.json"))
    ap.add_argument("--agents", default=",".join(rules.AGENTS))
    ap.add_argument("--probe", help="owner/repo#number: print one PR's claim and CI, write nothing")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("set GITHUB_TOKEN (read access to public repositories is enough)")
    gh = GitHub(token)
    if args.probe:
        return probe(gh, args.probe)
    if not args.aidev:
        sys.exit("--aidev is required")

    frame_sha = sha256_file(args.aidev)
    frame, text = load_frame(args.aidev)
    frame_tag = "aidev@" + frame_sha[:12]

    log = {"frame_file_sha256": frame_sha, "prereg_sha256": sha256_file(rules.PREREG),
           "started_at": now(), "agents": {}}
    if os.path.exists(args.log):
        with open(args.log) as f:
            log = json.load(f)
        if log["frame_file_sha256"] != frame_sha:
            sys.exit("scan_log.json was written for a different AIDev file; move it away to start over")
    log["frame_rows"] = {a: len(rows) for a, rows in frame.items()}

    # On a restart the counts toward the target come from data.csv, not from the log.
    done, per_repo, recorded, determinate = set(), {}, {}, {}
    if os.path.exists(args.out):
        with open(args.out, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add(row["row_id"])
                k = (row["agent"], row["repo"].lower())
                per_repo[k] = per_repo.get(k, 0) + 1
                recorded[row["agent"]] = recorded.get(row["agent"], 0) + 1
                if row["ci"] in ("success", "failure"):
                    determinate[row["agent"]] = determinate.get(row["agent"], 0) + 1
    new_file = not os.path.exists(args.out)
    out = open(args.out, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    if new_file:
        writer.writeheader()

    def save_log():
        log["updated_at"] = now()
        with open(args.log + ".tmp", "w") as f:
            json.dump(log, f, indent=1, sort_keys=True)
        os.replace(args.log + ".tmp", args.log)

    agents = args.agents.split(",")
    if not set(agents) <= set(rules.AGENTS):
        sys.exit(f"--agents must be a subset of {rules.AGENTS}")
    for agent in agents:
        st = log["agents"].setdefault(agent, {"position": 0, **{c: 0 for c in COUNTERS}, "stopped": ""})
        st["recorded"], st["determinate"] = recorded.get(agent, 0), determinate.get(agent, 0)
        rows = frame[agent]
        print(f"{agent}: frame {len(rows)}, resuming at {st['position']}", file=sys.stderr)
        while st["position"] < len(rows):
            if st["determinate"] >= rules.TARGET_PER_AGENT:
                st["stopped"] = "target reached"
                break
            if st["fetched"] >= rules.MAX_FETCH_PER_AGENT:
                st["stopped"] = "fetch budget used"
                break
            _key, idx, repo, number = rows[st["position"]]
            st["position"] += 1
            row_id = f"{agent}:{repo}#{number}"
            if row_id in done:
                continue
            title, body = text(idx)
            if rules.find_claim(title, body) is None:                       # step 1
                st["offline_no_claim"] += 1
                continue
            status, pr = gh.get(f"/repos/{repo}/pulls/{number}")             # step 2
            st["fetched"] += 1
            if status != 200:
                st["gone"] += 1
                save_log()
                continue
            claim = rules.find_claim(pr.get("title"), pr.get("body"))       # step 3
            if claim is None:
                st["claim_removed"] += 1
                save_log()
                continue
            cap_key = (agent, pr["base"]["repo"]["full_name"].lower())       # step 4
            if per_repo.get(cap_key, 0) >= rules.REPO_CAP:
                st["repo_cap"] += 1
                save_log()
                continue
            try:
                row = record_pr(gh, agent, row_id, pr, claim, frame_tag)     # step 5
            except CiUnreadable:
                st["ci_unreadable"] += 1
                save_log()
                continue
            writer.writerow(row)
            out.flush()
            done.add(row_id)
            per_repo[cap_key] = per_repo.get(cap_key, 0) + 1
            st["recorded"] += 1
            if row["ci"] in ("success", "failure"):
                st["determinate"] += 1
            print(f"  {row_id}: {row['ci']} ({st['determinate']}/{rules.TARGET_PER_AGENT})", file=sys.stderr)
            save_log()
        else:
            st["stopped"] = "frame exhausted"
        save_log()
    out.close()


if __name__ == "__main__":
    main()
