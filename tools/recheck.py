"""Recompute the machine-checkable numbers in results/score.md from this repo. Python stdlib + git only. Read-only.

  git clone https://github.com/NexumCorpus/night-adversary-sandbox && cd night-adversary-sandbox
  python3 -I tools/recheck.py                  # class counts, git column, blinding label
  python3 -I tools/recheck.py --nex /path/nex  # also re-run nex (Nexum-Graph 9d58f94) on every case

A fresh clone already has every case branch as origin/cNN-base and origin/cNN-b. Needs git 2.38+ (merge-tree --write-tree).
What this does NOT check: the CodeRabbit columns (flagged / self_break / false alarm) were scored by hand from results/raw;
see README.md. Exit status is 0 only if every check below passes.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

# Numbers published in results/score.md: class -> (n, git refused merge, nex flagged)
PUBLISHED = {"SIG": (3, 2, 3), "RENAME": (5, 2, 5), "CONTROL": (13, 0, 1)}
LABEL = re.compile(r"agent [AB]\b|unrelated", re.I)  # the self-labelling comment in the CONTROL plant
failures = []


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def check(ok, what):
    print(("PASS  " if ok else "FAIL  ") + what)
    if not ok:
        failures.append(what)


def resolve(repo, name):
    for cand in (f"origin/{name}", name):
        if git(repo, "rev-parse", "--verify", "-q", cand + "^{commit}").returncode == 0:
            return cand
    sys.exit(f"missing branch {name}: run  git fetch origin '+refs/heads/c*:refs/remotes/origin/c*'")


def nex_flagged(nex, repo, base, b):
    r = subprocess.run([nex, "check", base, b, "--repo-path", repo, "--format", "json"], capture_output=True, text=True)
    j = json.loads(r.stdout)
    return len(j.get("conflicts", j if isinstance(j, list) else [])) > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--nex", help="path to a nex binary built from Nexum-Graph 9d58f94")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    cases = [json.load(open(f, encoding="utf-8"))["case"] for f in sorted(glob.glob(os.path.join(repo, "results/raw/c*.json")))]
    rows = {k: [] for k in PUBLISHED}
    for c in cases:
        base, b = resolve(repo, c["n"] + "-base"), resolve(repo, c["n"] + "-b")
        mb = git(repo, "merge-base", base, b).stdout.strip()
        diff = git(repo, "diff", mb, b).stdout
        label = any(LABEL.search(l) for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
        mt = git(repo, "merge-tree", "--write-tree", base, b)
        if mt.returncode not in (0, 1):
            sys.exit("git merge-tree failed (git 2.38+ needed): " + mt.stderr.strip())
        nex = nex_flagged(a.nex, repo, base, b) if a.nex else None
        rows[c["kind"]].append((c, mt.returncode == 1, label, nex))
    for kind, (n, git_n, nex_n) in PUBLISHED.items():
        rs = rows[kind]
        check(len(rs) == n, f"{kind}: {len(rs)} cases (published {n})")
        conflicts = sum(r[1] for r in rs)
        check(conflicts == git_n, f"{kind}: git merge refused {conflicts} (published {git_n})")
        check(all(r[1] == r[0]["git_refused_merge"] for r in rs), f"{kind}: git result matches results/raw field in every case")
        labelled = sum(r[2] for r in rs)
        print(f"INFO  {kind}: {labelled}/{len(rs)} diffs add a self-labelling comment (disclosed blinding flaw; expect CONTROL all, others none)")
        check(labelled == (len(rs) if kind == "CONTROL" else 0), f"{kind}: self-labelling comment count as disclosed")
        if a.nex:
            flagged = sum(r[3] for r in rs)
            check(flagged == nex_n, f"{kind}: nex flagged {flagged} (published {nex_n})")
            check(all(r[3] == r[0]["nex_flagged"] for r in rs), f"{kind}: nex result matches results/raw field in every case")
    print("\n" + ("ALL CHECKS PASSED" if not failures else f"{len(failures)} CHECK(S) FAILED"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
