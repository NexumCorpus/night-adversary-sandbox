# False-green census of agent PRs: phase A results

## Findings

None yet: no pull requests have been collected, so there is no rate to report.

The pre-registration (`PREREG.md`), the collector, the verifier and their tests are in place. The
collection itself could not run where they were written. That environment's GitHub access covers only this
repository (no search, no GraphQL, no other repositories), and it cannot reach Hugging Face, where the AIDev
frame is hosted. Nothing on this page is an estimate, and no data has been made up to fill the gap.

When `data.csv` is filled, this section will give, per agent, the share of claim PRs whose own CI failed at
the head commit, with its 95% interval, before anything else.

## Results (computed by verify.py from data.csv)

<!-- verify.py:begin (generated from data.csv; do not edit by hand) -->

data.csv has 0 rows. There is nothing to report yet.

<!-- verify.py:end -->

## How to reproduce

From any machine with ordinary read access to the public GitHub API:

1. Download `all_pull_request.parquet` from the Hugging Face dataset `hao-li/AIDev` and install `pyarrow`.
2. `GITHUB_TOKEN=<read-only token> python3 census/collect.py --aidev all_pull_request.parquet`.
   It writes `data.csv` and `scan_log.json`, respects rate limits and can be restarted.
3. `python3 census/verify.py --hand-sample` lists the 30 pre-registered rows for the hand check. Fill
   `hand_label` (`claim` or `not_claim`) and `hand_note` for those rows in `data.csv`.
4. `python3 census/verify.py --write` rewrites the computed block; then write the Findings from it.
5. `python3 census/verify.py` must report no errors. It re-derives each row's CI from the stored check list,
   re-checks each snippet against its rule, and fails if any number above differs from `data.csv`.
6. `python3 -m unittest census/test_census.py` runs the rule tests.

## Limits

These hold for the planned data and are stated before any of it exists.

- **Claim precision** is checked by hand on a random 30 claim PRs (pending). Recall is not measured. The
  rules are conservative on purpose: a line that also mentions a failure, a negation or a condition is not
  counted, so claims made next to a caveat are missed.
- **Frame.** AIDev covers five agents and a fixed collection period that ends well before this census, and
  agents change quickly. Jules and other agents are not in it. AIDev's agent labels are used as given.
- **Survivorship.** PRs or repositories deleted since AIDev was built drop out, as do PRs whose current
  text no longer contains the claim.
- **CI "none" is excluded from n.** Repositories without CI, and PRs whose workflows were never approved
  (common for bot and fork PRs), leave the denominator. If those PRs differ, the rate shifts.
- **What "failure" means.** Any failing check at the head commit counts, including checks unrelated to the
  claim (a CLA bot, a deploy preview, a review bot). The core-CI rate removes the obvious ones with a fixed
  name list; it cannot remove all of them. Cancelled runs count as neutral.
- **Timing.** The primary rate pairs the current PR text with the CI of the current head commit. If commits
  were pushed after the claim was written, the claim may describe an earlier commit. The aligned-only rate
  addresses this only where the body's edit time is available.
- **Independence.** Wilson intervals treat PRs as independent. PRs from one repository share CI
  configuration; the cap of 2 PRs per agent and repository limits this but does not remove it.
- **Pooled row.** Each agent has the same target (75 PRs with a CI verdict), so the pooled row is not an
  estimate for agent PRs in general.
