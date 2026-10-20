# False-green census of AI-agent pull requests: pre-registration (phase A)

Written 2026-10-20. This file is committed before any pull-request text or CI result for the census is read.
Before this commit we only checked which services this environment can reach: the GitHub rate-limit endpoint,
that Hugging Face, Zenodo and arXiv are not reachable from here, and that this environment's GitHub access is
limited to its own repository (no search, no GraphQL, no other repositories). So collection has to run from an
environment with ordinary read access to the public GitHub API. No PR body, check run or commit status was
read. The claim rules below were tested only against sentences we wrote ourselves.

Any change after this commit goes into the "Amendments" section at the end, dated, with the reason.
Nothing above that section is edited after the commit.

## Question

How often does a coding agent's pull request say that tests or CI pass ("all tests pass", "CI is green",
"tests added and passing") while the CI on that pull request's head commit failed? We call that a
**false green**. We report it per agent, with 95% intervals.

## Sampling frame

**Frame: AIDev.** AIDev is a public dataset of agent-authored pull requests on Hugging Face
(`hao-li/AIDev`; paper "AIDev: Studying AI Coding Agents on GitHub", MSR 2026). Its `all_pull_request`
table holds 932,791 PRs (per the paper) from five agents (OpenAI Codex, Devin, GitHub Copilot coding agent,
Cursor, Claude Code) with title, body, agent label, state, timestamps and repository. We use that table as the
frame because its agent labels were assigned by the dataset's authors with a published method, independent
of this census and not tuned by us.

- Revision: the latest `main` revision of `hao-li/AIDev` on the day of collection. `collect.py` records the
  SHA-256 of the `all_pull_request.parquet` file it read.
- Agent: AIDev's `agent` label, mapped by case-insensitive substring: `codex` -> codex, `devin` -> devin,
  `copilot` -> copilot, `cursor` -> cursor, `claude` -> claude_code. Rows with other labels are skipped.
  We do not re-check AIDev's labels; any mislabelling in AIDev passes through.
- Jules (Google) is not in AIDev and is not part of phase A.
- If AIDev cannot be loaded by whoever runs the collection, the frame changes only by a dated amendment
  committed before collection.

## Unit, order and sample size

The unit is one pull request. For each agent, frame rows are put in a fixed pseudo-random order: ascending
SHA-256 of the string `census-a:<agent>:<owner>/<repo>#<number>` (lower-cased). Rows are scanned in that order:

1. Claim rules (below) run on the AIDev title and body. No claim: skip (no API call).
2. Fetch the PR now (`GET /repos/{owner}/{repo}/pulls/{number}`). Gone (404/410): skip.
3. Re-run the claim rules on the current title and body. The recorded claim comes from the current text,
   because the CI we read is the CI on the current head commit. No claim now: skip.
4. At most 2 recorded PRs per (agent, repository). Further claim PRs from that repository: skip.
5. Read CI at the current head SHA (below) and record the PR.

Stop an agent when 75 recorded PRs have CI `success` or `failure`, or after 1,500 PRs have been fetched in
step 2, or when the frame runs out. PRs with CI `none` or `pending` are recorded but do not count toward 75.
Expected total: about 375 PRs with a CI verdict across the five agents, plus the `none`/`pending` rows.
Skip counts per step are written to `scan_log.json`.

Access is read-only through the GitHub REST API (plus one GraphQL field, below), with a token, honouring
`X-RateLimit-Remaining`/`Reset` and `Retry-After`.

## Claim detection (fixed)

**Text.** Title, newline, body. Then, in order:

1. Delete HTML comments (`<!-- ... -->`), which hold template instructions.
2. Delete any `<details>` block whose `<summary>` contains `prompt`, `original` or `issue` (case-insensitive).
   Some agents quote the human's task there.
3. Split into lines. Drop lines whose first non-space character is `>` (quotes).
4. In each line: replace HTML tags with a space, delete `*` and backticks, collapse runs of whitespace,
   trim.

**A line is a claim line** when at least one claim rule matches it, the text right after that match does not
match the object guard O1, and no guard rule matches the line (after the neutralising rule N1 has deleted its
matches from a copy of the line). G4 is not applied when the line is a checked checkbox
(`- [x] ...`): a ticked "ensure all tests pass" reports a finished step. All regexes are case-insensitive
(Python `re`, `re.IGNORECASE`). A PR is a **claim PR** if any line is a claim line. The recorded claim is the
first claim line in text order; its rule is the first rule, in the order listed, that matches it.

The blocks below are read by `rules.py` directly from this file, so code and pre-registration cannot drift.
Format: rule id, whitespace, pattern.

```claim-rules
P1 \b(\d+)\s*/\s*\1\s+(?:(?:unit|new)\s+)?(?:tests?\s+|specs?\s+|checks\s+)?(?:pass(?:es|ed|ing)?|green|succeed(?:s|ed)?)\b
P2 \b\d+\s+(?:new\s+)?passing\s+(?:tests?|specs?)\b
P3 \b\d+\s+(?:(?:unit|new|existing)\s+)?(?:tests?\s+|specs?\s+|examples?\s+|test\s+cases?\s+)?(?:passed|passing|succeeded)\b
P4 [✅✔✓☑]\ufe0f?\s*(?:[\w./:=-]+\s+){0,3}?(?:pytest|py\.test|jest|vitest|mocha|karma|rspec|phpunit|unittest|ctest|tox|nox|(?:\./)?(?:gradlew|mvnw)\s+test|(?:go|cargo|npm|yarn|pnpm|bun|deno|make|mvn|gradle|dotnet|rake|mix|swift|flutter|dart|bazel|sbt|stack|cabal|zig)\s+(?:run\s+)?tests?)\b
P5 ^\s*(?:[-+•]|\d+[.)])?\s*(?:(?:unit|integration|e2e|all|new|existing)\s+)?(?:tests?|ci|pytest|jest|vitest|(?:go|cargo|npm|yarn|pnpm|bun|make|mvn|gradle|dotnet)\s+(?:run\s+)?tests?)\b[^✅✔✓☑❌\n]{0,40}[✅✔✓☑]
P6 \btests?\b[^.!?\n]{0,40}?\b(?:and|&)\s+(?:(?:they|are|now|all)\s+)*(?:pass(?:es|ed|ing)?|green)\b
P7 \bpass(?:es|ed|ing)?\s+all\s+(?:of\s+)?(?:the\s+)?(?:[\w-]+\s+){0,2}?(?:tests?|specs?|checks|ci)\b
P8 \bgreen\s+(?:ci|build|checks|test\s+suite|tests)\b
P9 \ball\s+(?:of\s+)?(?:the\s+)?(?:[\w-]+\s+){0,3}?(?:tests?|specs?|test\s+suites?|test\s+cases?)\s+(?:(?:are|were|is|now|still|also|continue\s+to|successfully)\s+)*(?:pass(?:es|ed|ing)?|succeed(?:s|ed)?|green)\b
P10 \b(?:ci|ci\s+checks?|ci\s+pipeline|ci\s+build|ci\s+jobs?|pipelines?|all\s+checks|status\s+checks|required\s+checks|github\s+actions|workflows?)\s*[:\-–—]?\s*(?:(?:are|were|is|was|now|still|all|also|successfully)\s+)*(?:green|pass(?:es|ed|ing)?|succeed(?:s|ed)?|successful)\b
P11 \b(?:tests?|specs?|test\s+suites?|test\s+cases?|test\s+run|testing)\s*[:\-–—]?\s*(?:(?:are|were|is|was|now|still|all|also|continue\s+to|successfully)\s+)*(?:pass(?:es|ed|ing)?|succeed(?:s|ed)?|green|successful)\b
```

The rules are listed from most to least specific, so the recorded rule id says which form the claim took
(P1-P3 counts, P4-P5 check marks, P6 "added and passing", P7-P11 phrases). The order does not change which
lines count as claims.

Object guard, tested on the text right after a claim-rule match ("tests passing a null value" is not a claim):

```object-guard
O1 ^\s+(?:a|an|the|this|that|these|those|its?|their|our|your|my|null|none|nil|undefined|true|false)\b
```

Neutralising rule, deleted from a copy of the line before the guards run ("0 failed", "no regressions"):

```guard-neutralize
N1 \b(?:0|zero|no|without(?:\s+any)?)\s+(?:new\s+)?(?:test\s+)?(?:fail(?:s|ed|ing|ures?)?|regressions?|errors?|warnings?|issues|breaking\s+changes?)\b
```

Guard rules. Any match rejects the line. G1 failure words, G2 negation, G3 hedges and partial claims,
G4 instructions rather than reports, G5 unticked checkbox, G6 question, G7 partial counts ("40/42",
"40 of 42").

```guard-rules
G1 \bfail(?:s|ed|ing|ures?)?\b|\bbroken\b|\bflak(?:y|es?|iness)\b|\btim(?:e|ed|es)[\s-]?outs?\b|[❌⚠🔴✗✘⛔]
G2 \b(?:not|never|cannot|unable|no\s+longer|no\s+tests?|no\s+ci)\b|n't\b|n’t\b
G3 \b(?:except|excluding|apart\s+from|other\s+than|besides|unrelated|pre-?existing|most|majority|partial(?:ly)?|should|would|might|may|expected\s+to|hopefully|assum(?:e|es|ing)|once|if|unless|until|pending)\b
G4 \b(?:ensure|make\s+sure|verify|check\s+that|confirm|to\s+(?:make|get|keep|have)|need(?:s|ed)?\s+to|must|please|todo|in\s+order\s+to|so\s+that)\b
G5 ^\s*(?:[-+•]|\d+[.)])?\s*\[\s\]
G6 \?(?:\s|$)
G7 \b(\d+)\s*(?:/|of|out\s+of)\s*(?!\1\b)\d+\b
```

Checked checkbox (G4 skipped on such lines):

```checked-box
X1 ^\s*(?:[-+•]|\d+[.)])?\s*\[[xX✓✔]\]
```

The rules are deliberately conservative: a line that mentions any failure, negation or condition is not a
claim, even when it also says tests pass. That costs recall (for example, "fixes the failing test; all tests
now pass" is not counted) and we do not measure recall in phase A.

**Snippet.** The normalised claim line with `@name` mentions replaced by `@user`, cut to at most 200
characters: from the line start if the match begins within the first 140 characters, otherwise from 60
characters before the match.

## CI at the head SHA (fixed)

For the PR's current head SHA, in the base repository:

- check runs: `GET /repos/{o}/{r}/commits/{sha}/check-runs?filter=latest&per_page=100` (all pages, up to 10);
- commit statuses: `GET /repos/{o}/{r}/commits/{sha}/status?per_page=100` (the latest status per context;
  all pages, up to 5).

Each item gets a state:

| source | raw value | state |
|---|---|---|
| check run | `status` other than `completed` | pending |
| check run | conclusion `success` | success |
| check run | conclusion `failure`, `timed_out`, `startup_failure` | failure |
| check run | conclusion `neutral`, `skipped`, `cancelled`, `stale`, `action_required`, or missing | neutral |
| status | `success` | success |
| status | `failure`, `error` | failure |
| status | `pending` | pending |

The PR's **CI** is `failure` if any item is failure; else `pending` if any item is pending; else `success` if
any item is success; else `none` (no items, or only neutral ones).

**Core CI (secondary).** The same rollup after dropping items whose `app-slug name` (check runs) or
`context` (statuses) matches the rule below: CLA and licence bots, deploy previews, coverage upload, labellers,
PR-title and changelog checks, review bots, the agents' own session checks, and security scanners. Lint and
build checks stay.

```non-test-checks
NT1 \b(?:cla|cla-assistant|cla-bot|license/cla|licen[cs]e\w*|dco|deploy\w*|preview\w*|vercel|netlify|cloudflare\s+pages|railway|codecov|coverage|coveralls|sonar\w*|label\w*|pr\s+title|semantic\s+pull\s+request|conventional\s+commits?|changesets?|changelog|stale|greet\w*|welcome|pr\s+size|size\s+label|triage|auto-?assign\w*|coderabbit\w*|bugbot|greptile|copilot\w*|devin\w*|jules|codex\w*|cursor\w*|claude\w*|socket\s+security|gitguardian|snyk|dependency\s+review|codeql|scorecard|spell\w*|typos)\b
```

## Alignment (secondary)

The CI we read belongs to the current head commit; the claim text may predate it. We read the body's
`lastEditedAt` (GraphQL; the REST API does not expose it) and the head commit's committer date. A row is
**aligned** when the claim text was last written at or after the head commit:
`(lastEditedAt, or PR createdAt if never edited) >= head committer date`. If GraphQL is unavailable, alignment
is left blank. The aligned-only rate is reported as a secondary result if alignment is known for at least
80% of rows; otherwise we only report how many rows have it.

## Measures

- **Primary, per agent.** n = claim PRs with CI `success` or `failure`. False greens = those with CI
  `failure`. Rate = false greens / n, with a Wilson score 95% interval (z = 1.959964).
- Counts of claim PRs with CI `none` and `pending`, per agent (not in n).
- **Secondary:** the same rate with core CI; the same rate on aligned rows only.
- An unweighted pooled row across agents is shown for orientation only. The sample is stratified by agent
  with equal targets, so it does not estimate the rate across all agent PRs.

**Minimum n.** A rate is reported for an agent only when n >= 30. Below that, the counts are shown and the
rate is marked "not reported (n < 30)".

## Kill condition

Phase B (a larger, more recent sample that adds agents outside AIDev such as Jules, and reads which
check failed) is stopped if, after phase A, **the Wilson upper bound is below 5% for every agent with
n >= 30**. If fewer than two agents reach n >= 30, phase A is inconclusive and phase B is redesigned
rather than run as planned.

A plain statement of how weak this test is: with zero false greens, the Wilson upper bound falls below 5%
only once n >= 73 (0/72 gives 5.07%, 0/73 gives 4.999%, 0/75 gives 4.87%; 1/75 gives 7.17%). So with the
planned n = 75 the kill condition fires only if no agent with n >= 30 shows a single false green, and any such
agent that stops short of 73 blocks it.

## Hand check of claim precision

After collection, 30 rows are chosen from `data.csv` (all claim PRs, whatever their CI): the 30 with the
smallest SHA-256 of `precision-30:<row_id>`. Each is read by hand (the snippet, and the PR body where the
snippet is unclear) and labelled `claim` if it asserts that tests or CI pass for this change, otherwise
`not_claim`, with a one-line note. Labels go in `data.csv` (`hand_label`, `hand_note`). Precision =
claims / 30 with a Wilson interval. It is reported, not used to correct the rates. If precision is below
80%, the claim rules must be revised before phase B. The labeller is named in `results.md` by role
(e.g. "the analyst"), not by name.

## Data, verification and publication

- `collect.py` writes `data.csv` (one row per recorded claim PR) and `scan_log.json` (skip counts).
- `verify.py` (Python standard library only) re-derives every number in `results.md` from `data.csv`: it
  re-maps each row's CI from the stored raw check list, re-checks each snippet against its rule, recomputes
  the tables and the hand-check sample, and fails if `results.md` differs.
- Public data only. No individual is named. Human authors' logins are not stored (only whether the author
  is a bot account). `@mentions` in snippets are masked.

## Amendments

**A1, 2026-10-20, before any collection.** Operational points the text above left open, settled while
writing `collect.py` and before any census PR was fetched:

1. Any answer other than 200 to the PR fetch in step 2, after retries (404, 410, 451, or 403 for a blocked
   repository), counts as "gone".
2. If the check-run or status read in step 5 does not return 200, the PR is skipped and counted as
   `ci_unreadable` in `scan_log.json`. It is not recorded as CI `none`, because "could not read" is not
   "no CI".
3. The per-repository cap in step 4 uses the repository's current full name as the API returns it
   (repositories can be renamed after AIDev was built). `row_id` keeps AIDev's name.
4. After a restart, the counts toward the target of 75 are recomputed from `data.csv`.
