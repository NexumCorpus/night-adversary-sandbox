# night-adversary-sandbox

Baseline arm for the Night Adversary experiment (E:/station/prophet/night-adversary).
Planted cross-PR breaks (SIG = signature change, RENAME = renamed symbol, CONTROL = harmless body change) are replayed here as
pull requests so an AI review bot (CodeRabbit) can review them. We count which planted breaks the bot flags and compare against
`nex` and `git merge` on the same cases. The kill rule was frozen before any bot output existed: after 14 nights, `nex` must not
catch fewer planted breaks than the best review bot in 2 of 3 classes.

Code in PRs comes from public merged PRs (each PR names its source and license). Nothing here is meant to run.
Built by Claude, directed by NexumCorpus.
