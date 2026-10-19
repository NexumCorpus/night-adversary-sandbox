# night-adversary-sandbox

Baseline arm for the Night Adversary experiment (E:/station/prophet/night-adversary).
Planted cross-PR breaks (SIG = signature change, RENAME = renamed symbol, CONTROL = harmless body change) are replayed here as
pull requests so an AI review bot (CodeRabbit) can review them. We count which planted breaks the bot flags and compare against
`nex` and `git merge` on the same cases. The kill rule was frozen before any bot output existed: after 14 nights, `nex` must not
catch fewer planted breaks than the best review bot in 2 of 3 classes.

Code in PRs comes from public merged PRs (each PR names its source and license). Nothing here is meant to run.
Built by Claude, directed by NexumCorpus.

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
