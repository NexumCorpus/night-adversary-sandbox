# CodeRabbit baseline: score (2026-10-19, scored by Assay #11 by hand under the pre-registered rule)

21 cases replayed as PRs #2-#22 (c01-c21). Raw reviews are in `raw/`. Every PR got a CodeRabbit review within about 3 minutes,
so the "no review" count is 0. Before counting, c01 and c02 were read by hand (Assay #9), then all 21.

| class | n | CodeRabbit flagged (A's call) | CodeRabbit self_break only | nex flagged | git refused merge |
|---|---|---|---|---|---|
| SIG | 3 | **0/3** | 0/3 | 3/3 | 2/3 |
| RENAME | 5 | **0/5** | 4/5 (c02, c11, c17, c19) | 5/5 | 2/5 |
| CONTROL (false alarm) | 13 | **0/13** (1 nit: c15) | n/a | 1/13 (c15) | 0/13 |

**Reading.** CodeRabbit never named agent A's new call: not in any SIG case and not in any RENAME case. On SIG it said outright that
nothing was left broken (c01: "No outdated repository caller is left by the argument change"; c07, c08 and c16 are similar). On 4 of
the 5 RENAME cases it caught B's own stale `import` (self_break), a break that exists without A. Scored both ways, it flags
0/8 cross-PR breaks under the strict rule and 4/8 if self_break counts. nex flagged 8/8, with 1 false alarm in 13 controls.
git flagged 4/8.

**Caveats, stated plainly.**
- The n is small: 3 SIG, 5 RENAME, 13 CONTROL. One sandbox, one bot, one night of replay, CHILL review profile, free-tier
  allowance (10 reviews/h).
- **Blinding flaw found while scoring:** the CONTROL plant (`adversary.py` line 205) inserts `_nx_trace = None  # agent B: unrelated change`.
  That comment is in all 13 CONTROL diffs, and CodeRabbit quoted it in c15. It tells a reader the change is unrelated, which favours
  the bot on false alarms. It does not affect SIG or RENAME, where the bot missed every cross-PR break anyway. Fix the plant
  (neutral comment, or none) before any larger-n run.
- nex and git are re-counted from `ledger-v2.jsonl` on this same subset (`nex_flagged`, `git_refused_merge` in `bot-replay.jsonl`).
- The kill rule (14 nights, nex not below the best bot in 2 of 3 classes) is not decided by this one baseline. On this sample nex is
  not below CodeRabbit in any class.
