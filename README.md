# night-adversary-sandbox

Baseline arm for the Night Adversary experiment. The experiment's own scripts and ledger are not published; see
[What is and is not in this repo](#what-is-and-is-not-in-this-repo).
Planted cross-PR breaks (SIG = signature change, RENAME = renamed symbol, CONTROL = harmless body change) are replayed here as
pull requests so an AI review bot (CodeRabbit) can review them. We count which planted breaks the bot flags and compare against
`nex` ([Nexum Graph](https://github.com/NexumCorpus/Nexum-Graph), commit `9d58f94`) and `git merge` on the same cases. The kill rule
was frozen before any bot output existed: after 14 nights, `nex` must not catch fewer planted breaks than the best review bot in 2 of
3 classes. The public record of that freeze is this repo's first commit (`b86c7f5`, 2026-10-19 19:01Z), which precedes the first case
PR (19:12Z); an earlier 2026-10-11 freeze is recorded only in an unpublished local history and cannot be checked from here.

Code in PRs comes from public merged PRs (each PR names its source and license; [results/sources.md](results/sources.md) lists the
upstream commits). The one script meant to run is [`tools/recheck.py`](tools/recheck.py).
Built by Claude, directed by NexumCorpus. The sections below the pre-registered rule were added on 2026-10-20 after an outside
reproduction (PR #23); the pre-registered text itself is unchanged.

## Pre-registered scoring rule (written 2026-10-19, before any case PR was opened or any bot output on a case was read)

**Setup per case.** Branch `cNN-base` holds the source repo's tree right after agent A's real PR merged (parent: the tree just
before it). Branch `cNN-b` holds agent B's planted change, forked from the tree *before* A merged. PR `cNN-b -> cNN-base` therefore
shows the reviewer exactly B's diff on top of a codebase that already contains A's new call. This is the same pair `nex check A B`
saw. A `.coderabbit.yaml` (review all base branches) is the only file added; it is outside every diff.

**Cases.** Every graded SIG/RENAME case in `ledger-v2.jsonl` (nex 9d58f94, nights 10-12 to 10-17) whose source repo carries a license
that permits redistribution, plus CONTROL cases from licensed repos. Unlicensed repos are skipped, and so are repos that were deleted.
nex and git are re-counted on this same subset.

**Flagged (SIG, RENAME).** The bot flags a case if any comment it posts within 30 minutes of the PR opening (the summary or an
inline comment; first review only, never after we reply) identifies a concrete call that this PR leaves broken. That means it
names the call site left un-updated (A's file or function) or states that the target symbol still has a caller that this
change breaks. These do NOT count: restating the change ("renames X to X_v2"); generic advice such as "make sure all callers
are updated" without a concrete call, which is recorded as `hedge`; and a merge-conflict notice, which counts in git's column.
**False alarm (CONTROL).** A comment claiming that the change breaks a call or behaviour. Style or unused-variable notes are `nit`,
not false alarms.
**No review** within 30 min = not flagged; reported separately.

**Procedure.** Raw review JSON (reviews, inline comments, issue comments) is saved to `results/raw/`. At least two raw reviews are read
by hand before any counting. The counts go in `results/score.md` per class: bot vs nex vs git. Small n is stated plainly.
Kill rule unchanged (frozen 2026-10-11; see above).

**Selection (fixed before the first case PR).** All licensed SIG/RENAME cases. For CONTROL, the first case per source repo,
skipping mlflow/mlflow, Azure/azure-devops-cli-extension and oss-slu/SpeechTranscription, which are too large to push whole.
That gives 21 cases: 3 SIG, 5 RENAME, 13 CONTROL. PR titles are neutral, and the case label never appears in a branch, title or commit.
Script: `replay_bot.py` in the Night Adversary directory (plan / push / fetch).

**Clarification, 2026-10-19 ~19:30Z, written after reading the raw reviews of c01 and c02 (and no others).** The RENAME plant
(`adversary.py mutate`) renames the def and every call, but not `import` lines. In 10 of the 15 graded RENAME cases, B's branch therefore
keeps a stale `from m import old_name` and is broken without A (c02's review caught exactly that). A comment that names only B's own
stale import is recorded as `self_break`, NOT flagged. This follows the rule above (A's call site), but it is stated here because
c02 prompted it. Scores are reported both ways.

## What is and is not in this repo

| In this repo | What it is |
|---|---|
| branches `cNN-base`, `cNN-b` | the 21 case pairs. PRs #2-#22 are their replays, reviewed by CodeRabbit; they are experiment records, not open work |
| `results/raw/` | raw bot output per PR (reviews, inline and issue comments) and the per-case record, including `nex_flagged` and `git_refused_merge` |
| `results/score.md` | the hand score under the pre-registered rule |
| `results/sources.md` | the upstream commit behind every case, and how to compare |
| `tools/recheck.py` | recomputes the class counts, the git column, the blinding label and (with `--nex`) the nex column |

Not published: `adversary.py` (plants the changes), `replay_bot.py` (selection and push), `ledger-v2.jsonl` and `bot-replay.jsonl`
(the private ledger of every graded case, nights 10-12 to 10-17, and the replay record). The plant script changed after these cases
were generated (the self-labelling comment was removed from the CONTROL plant on 2026-10-19), so the current file would not describe
them, and the ledger lists skipped third-party repositories and local paths. A matching revision and a redacted ledger could be
published later. Until then:

- The selection claims (every licensed SIG/RENAME case; the first CONTROL per source repo) cannot be re-derived from this repo.
  On 2026-10-20 the selection rule was re-run against the private ledger and returns exactly these 21 cases, in this order. For
  nights 10-12 to 10-17 the ledger holds 15 graded RENAME and 8 graded SIG cases. The published 5 and 3 are the licensed ones; of
  the rest, 9 RENAME and 5 SIG have no licence and 1 RENAME has an unknown licence (repository gone).
- How each planted change was produced is documented only by the diffs themselves.
- The scoring of the CodeRabbit columns is by hand, from `results/raw`. Anyone can re-read those reviews and re-score them.

## Reproduce

```
git clone https://github.com/NexumCorpus/night-adversary-sandbox && cd night-adversary-sandbox
python3 -I tools/recheck.py
```

Needs git 2.38 or newer and Python 3. It checks the class counts (3 SIG, 5 RENAME, 13 CONTROL), the git column (`git merge-tree`:
2/3, 2/5, 0/13) and the blinding label (present in 13/13 CONTROL diffs, in none of the SIG and RENAME diffs), and prints PASS or FAIL
for each. To add the nex column (3/3, 5/5, 1/13), build nex from the public commit and pass it in:

```
git clone https://github.com/NexumCorpus/Nexum-Graph && cd Nexum-Graph && git checkout 9d58f94
cargo build --release --locked -p nex-cli
cd ../night-adversary-sandbox && python3 -I tools/recheck.py --nex ../Nexum-Graph/target/release/nex
```

Run on 2026-10-20 on Ubuntu 24.04 (WSL, git 2.43.0, Python 3.12.3) from a fresh clone, with nex built from `9d58f94` (the build
took 1 min 23 s): all checks passed and `git status` stayed clean. Not covered: the CodeRabbit columns (see above).

## Errata and clarifications (added 2026-10-20)

An outside reproduction (PR #23) found the following. The pre-registered text above is unchanged; corrections to `results/score.md`
are listed at the bottom of that file.

1. **Clarification timestamp.** The clarification says "~19:30Z". Its commit (`bb17caa`) is stamped 19:19:11Z. The bot had already
   posted on c03 at 19:17:51Z. "And no others" (only c01 and c02 read before it was written) is self-reported and cannot be checked.
2. **"10 of the 15 graded RENAME cases".** The 15 is the private ledger's count of graded RENAME cases for nights 10-12 to 10-17; the
   10 cannot be checked from this repo. In the 5 published RENAME cases, 4 (c02, c11, c17, c19) still import the old name in B's tree
   (`git grep -w` on `cNN-b`); c08 does not.
3. **Kill rule and CONTROL.** The frozen rule counts "planted breaks", and CONTROL has none, so it does not say how CONTROL is
   compared. On catches, nex and the bot are level (0 and 0); on false alarms nex is behind (1/13 against 0/13). On this sample nex
   is ahead in SIG (3/3 against 0/3) and RENAME (5/5 against 0/5), which is 2 of 3 classes under either reading. The sentence "nex
   is not below CodeRabbit in any class" holds only under the first reading. The rule itself is unchanged, and one baseline does not
   decide it.
4. **What the bot could see.** The CONTROL plant adds `_nx_trace = None  # agent B: unrelated change` to 13/13 CONTROL diffs and to
   none of the 8 SIG/RENAME diffs; that was disclosed in `results/score.md`. Other cues exist and are the same kind for every class:
   all case commits are authored `night-adversary`; every PR body says it is replayed for a review-bot study; the plants share names
   (`_nx_trace`, `nx_mode`, `_v2`). Titles follow one template per class (CONTROL "Add trace placeholder in ...", SIG "Add required
   nx_mode parameter to ... and update callers", RENAME "Rename ... to ..._v2 and update callers"). "Titles are neutral" in the
   pre-registered text means no class word appears, which is true; it does not mean the titles are alike across classes. Whether
   "and update callers" makes the bot less likely to flag SIG and RENAME is untested. The label falls on the class where the bot leads
   nex, so the CONTROL row is not a clean false-alarm comparison. The 13 branches still carry the label (they are experiment
   records and are not edited). The generator no longer writes it (changed 2026-10-19); no review-bot run has used the fixed plant yet.
5. **`.coderabbit.yaml`.** It is added in 19 of the 21 snapshots. In c19 and c20 (NetAlertX) upstream already had its own, which the
   sandbox file replaces; see `results/sources.md`. It is outside every diff in all cases.
6. **Process claims.** "Read by hand" and "scored by hand" are self-reported. The raw reviews they rest on are in `results/raw`.
7. **"The same pair `nex check A B` saw".** The experiment ran nex on local branches (A merged, and B). `tools/recheck.py --nex` runs
   `nex check cNN-base cNN-b` on the published branches and, on the same pairs, gives the recorded result in 21 of 21
   cases.
