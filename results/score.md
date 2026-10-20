# CodeRabbit baseline: score (2026-10-19, scored by hand by a Claude session under the pre-registered rule)

21 cases replayed as PRs #2-#22 (c01-c21). Raw reviews are in `raw/`. Every PR got a CodeRabbit review within 5.5 minutes of opening (median 2.6),
so the "no review" count is 0. Before counting, c01 and c02 were read by hand, then all 21.

| class | n | CodeRabbit flagged (A's call) | CodeRabbit self_break only | nex flagged | git refused merge |
|---|---|---|---|---|---|
| SIG | 3 | **0/3** | 0/3 | 3/3 | 2/3 |
| RENAME | 5 | **0/5** | 4/5 (c02, c11, c17, c19) | 5/5 | 2/5 |
| CONTROL (false alarm) | 13 | **0/13** (1 nit: c15) | n/a | 1/13 (c15) | 0/13 |

**Reading.** CodeRabbit never named agent A's new call: not in any SIG case and not in any RENAME case. On SIG it said outright that
nothing was left broken (c01: "No outdated repository caller is left by the argument change"; c07 and c16 are similar; c08, a RENAME case, said the same: "updates all repository references"). On 4 of
the 5 RENAME cases it caught B's own stale `import` (self_break), a break that exists without A (the fifth, c08, has no stale import in B's tree, so a self-break existed in 4 of 5 and the bot found all 4). Scored both ways, it flags
0/8 cross-PR breaks under the strict rule and 4/8 if self_break counts. nex flagged 8/8, with 1 false alarm in 13 controls.
git flagged 4/8.

**Caveats, stated plainly.**
- The n is small: 3 SIG, 5 RENAME, 13 CONTROL. One sandbox, one bot, one night of replay, CHILL review profile, the plan's 10 included
  reviews per hour (the bot reports "Plan: Advanced").
- **Blinding flaw found while scoring:** the CONTROL plant (`adversary.py` line 205) inserts `_nx_trace = None  # agent B: unrelated change`.
  That comment is in all 13 CONTROL diffs, and CodeRabbit quoted it in c15. It tells a reader the change is unrelated, which favours
  the bot on false alarms. The label is absent from the SIG and RENAME diffs, where the bot missed every cross-PR break; other cues the bot could see are listed in
  the README (errata, item 4). The label falls on the class where the bot leads nex (0/13 against 1/13 false alarms), so the CONTROL row
  is not a clean comparison. Fix the plant
  (neutral comment, or none) before any larger-n run.
- nex and git are recorded per case in `raw/` (`nex_flagged`, `git_refused_merge`). `tools/recheck.py` recomputes git, and with `--nex`
  nex (built from Nexum Graph `9d58f94`). The private ledger they were first counted from is not published.
- The kill rule (14 nights, nex not below the best bot in 2 of 3 classes) is not decided by this one baseline. On this sample nex is
  ahead in SIG and RENAME, which is 2 of 3 classes. In CONTROL it is level on catches (0 and 0) and behind on false alarms (1/13 against
  0/13), and the frozen rule does not say which comparison applies (README, errata item 3).

## Corrections (2026-10-20, after an outside reproduction; PR #23)

The text above was edited in place only where listed here. The scored numbers did not change.

| where | was | now |
|---|---|---|
| title, and the line on reading c01 and c02 | session labels of the two Claude sessions that scored and read the reviews | "a Claude session" |
| review latency | "within about 3 minutes" | within 5.5 minutes of opening (median 2.6, 13 of 21 within 3.0) |
| Reading, SIG | "c07, c08 and c16 are similar" (c08 is a RENAME case) | c07 and c16 are SIG; c08 is named as a RENAME case |
| Reading, RENAME | no mention of c08's stale import | c08 has none: a self-break existed in 4 of 5 and the bot found all 4 |
| caveat, allowance | "free-tier allowance (10 reviews/h)" | the plan's 10 included reviews per hour; the bot reports "Plan: Advanced" |
| caveat, blinding | "It does not affect SIG or RENAME" | the label is absent from those diffs, but other cues exist (README, errata item 4); the label falls on the class where the bot leads |
| caveat, re-count | "re-counted from `ledger-v2.jsonl`" (not public) | recorded in `raw/` and recomputed by `tools/recheck.py` |
| last caveat | "nex is not below CodeRabbit in any class" | ahead in SIG and RENAME; CONTROL depends on which comparison the frozen rule means |

