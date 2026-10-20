# Sources of the 21 cases

Each case is a real merged pull request in a public repository. `cNN-base` is the source repo's tree right after that PR merged
(its upstream merge commit); the parent of `cNN-base`, and of `cNN-b`, is the tree just before it (the merge commit's first parent).
On 2026-10-20 all 21 snapshots were compared with the upstream commits through the GitHub API, file by file and blob hash by blob hash
(submodule links included): they are identical to upstream, except that every snapshot carries the sandbox's `.coderabbit.yaml`.
For c19 and c20 (NetAlertX) upstream already had its own `.coderabbit.yaml` (176 bytes); the sandbox file replaces it in the snapshot
(it is outside every diff, since base and `-b` carry the same file). For the other cases the file is added.

To check one case yourself (empty output means identical; replace the repo and SHA from the table):

```
git remote add up https://github.com/calegeffre/WhatTheFed && git fetch -q up b83a71d98c7d44fbf8597fe50198090424d6b075
git diff --stat b83a71d98c7d44fbf8597fe50198090424d6b075 origin/c01-base -- . ':!.coderabbit.yaml'
```

| case | kind | source pull request | license | upstream merge commit (= `cNN-base` tree) | its first parent (= tree before A) |
|---|---|---|---|---|---|
| c01 | SIG | [calegeffre/WhatTheFed#4](https://github.com/calegeffre/WhatTheFed/pull/4) | MIT | `b83a71d98c7d44fbf8597fe50198090424d6b075` | `9e64ee43eb5d66d35a52d96ded96b02d326fbd52` |
| c02 | RENAME | [calegeffre/WhatTheFed#4](https://github.com/calegeffre/WhatTheFed/pull/4) | MIT | `b83a71d98c7d44fbf8597fe50198090424d6b075` | `9e64ee43eb5d66d35a52d96ded96b02d326fbd52` |
| c03 | CONTROL | [calegeffre/WhatTheFed#4](https://github.com/calegeffre/WhatTheFed/pull/4) | MIT | `b83a71d98c7d44fbf8597fe50198090424d6b075` | `9e64ee43eb5d66d35a52d96ded96b02d326fbd52` |
| c04 | CONTROL | [brabster/xubuntu-workstation#99](https://github.com/brabster/xubuntu-workstation/pull/99) | MIT | `46b28bf786ae44924b5190912432e4e0abeb5bed` | `43c113f46856e27be309f2cb9383cab82c24e368` |
| c05 | CONTROL | [Prince-1005/Pinak-CLI#3](https://github.com/Prince-1005/Pinak-CLI/pull/3) | MIT | `81c6acf1fd4e533eee5a787fa33da0ae0f675882` | `fb9571c4eeb9ae2e2dd15b9e837cec4ede37e8c8` |
| c06 | CONTROL | [vananhnt994/theodor-family-content-creator#4](https://github.com/vananhnt994/theodor-family-content-creator/pull/4) | Apache-2.0 | `22f625237dd150fccfb26dc55d8168b2d812b064` | `900554237b3f8adb29d6e583f7d42bc833cd3892` |
| c07 | SIG | [PriyanshKuniyal/CortexView#3](https://github.com/PriyanshKuniyal/CortexView/pull/3) | MIT | `89c0b71cd40ad0992121e21ae948fbcc4ee1242f` | `592a1b4781c0bb389e29c2446fce7a516df9c86c` |
| c08 | RENAME | [PriyanshKuniyal/CortexView#3](https://github.com/PriyanshKuniyal/CortexView/pull/3) | MIT | `89c0b71cd40ad0992121e21ae948fbcc4ee1242f` | `592a1b4781c0bb389e29c2446fce7a516df9c86c` |
| c09 | CONTROL | [PriyanshKuniyal/CortexView#3](https://github.com/PriyanshKuniyal/CortexView/pull/3) | MIT | `89c0b71cd40ad0992121e21ae948fbcc4ee1242f` | `592a1b4781c0bb389e29c2446fce7a516df9c86c` |
| c10 | CONTROL | [azman0101/ha-ecoflow#11](https://github.com/azman0101/ha-ecoflow/pull/11) | Apache-2.0 | `712ddc2ab3fbc9c00e208659fa6ea2674735b4f7` | `780ef14660183ee1e3059eaf26b07018c643e8d9` |
| c11 | RENAME | [rajesh0042/agent-framework#2](https://github.com/rajesh0042/agent-framework/pull/2) | MIT | `06afaa562956e5100efa75729e2defcd24bf74fc` | `023b686433dc572e873217be091c968e45d9b6c7` |
| c12 | CONTROL | [rajesh0042/agent-framework#2](https://github.com/rajesh0042/agent-framework/pull/2) | MIT | `06afaa562956e5100efa75729e2defcd24bf74fc` | `023b686433dc572e873217be091c968e45d9b6c7` |
| c13 | CONTROL | [clavicarius/HomeLab-compose#66](https://github.com/clavicarius/HomeLab-compose/pull/66) | MIT | `4445cbaac9912ced7c21770578f7ef9b32bd26c9` | `99cf21ee8eca97dfcd66b0d8a9726ca48489967a` |
| c14 | CONTROL | [Colin955023/MinecraftServerManager#71](https://github.com/Colin955023/MinecraftServerManager/pull/71) | GPL-3.0 | `ea8eed7032f96a4aa0dc0f5e5f42d46f3ba4430e` | `cfe38321252af217fd4bb793d4c2ad4b35547b32` |
| c15 | CONTROL | [rikardronnkvist/Tautulli-MCP#3](https://github.com/rikardronnkvist/Tautulli-MCP/pull/3) | MIT | `dfbab289cc494cc67df9d24b35c10916de5a857a` | `cbecaa5f936a0d5605ceb4818aa5db080ef01b29` |
| c16 | SIG | [rikardronnkvist/Tautulli-MCP#2](https://github.com/rikardronnkvist/Tautulli-MCP/pull/2) | MIT | `cbecaa5f936a0d5605ceb4818aa5db080ef01b29` | `a28c5f9ac3bf86e42d458709bc91ae66417769a6` |
| c17 | RENAME | [rikardronnkvist/Tautulli-MCP#2](https://github.com/rikardronnkvist/Tautulli-MCP/pull/2) | MIT | `cbecaa5f936a0d5605ceb4818aa5db080ef01b29` | `a28c5f9ac3bf86e42d458709bc91ae66417769a6` |
| c18 | CONTROL | [kellerza/hass-addons#84](https://github.com/kellerza/hass-addons/pull/84) | Apache-2.0 | `1f54aac4da79a43b9863c67ba37b5f29d116e0ca` | `10703826537d64e739ff5a06f75ce15b9027181a` |
| c19 | RENAME | [netalertx/NetAlertX#1738](https://github.com/netalertx/NetAlertX/pull/1738) | GPL-3.0 | `6208e00dd8be63756ab9ca99a4d1974bcc1718d7` | `edae72934634c0703db600d97204a1e3a4bbef2d` |
| c20 | CONTROL | [netalertx/NetAlertX#1738](https://github.com/netalertx/NetAlertX/pull/1738) | GPL-3.0 | `6208e00dd8be63756ab9ca99a4d1974bcc1718d7` | `edae72934634c0703db600d97204a1e3a4bbef2d` |
| c21 | CONTROL | [vulnerability-lookup/vulnerability-lookup#328](https://github.com/vulnerability-lookup/vulnerability-lookup/pull/328) | AGPL-3.0 | `3c58c1c04102cca5433d82442d1fff178b4abb4e` | `10186109643bdc4e327abd596fc7ba9735a5bf03` |
