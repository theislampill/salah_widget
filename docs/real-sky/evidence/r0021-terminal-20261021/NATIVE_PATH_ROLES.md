# Native evidence path roles

Host aliases identify provenance only; they are not runnable public paths. `${WORK_ROOT}` is the isolated evidence/build root; `${REPO_ROOT}` is the isolated PR worktree; `${BROWSER_CACHE}` is the existing test-browser executable cache; `${TOOL_CACHE}` is the existing Node/tool package cache; `${STDLIB_PYTHON}` is the standard-library Python installation; `${QA_TOOLCHAIN}` is the existing Python/Node QA toolchain root. No private browser profile is published.

Use the repository-native source/test commands and the public manifest mappings. A projected original/local-only locator is not a promise that an external executor has that local file. The scripts retain the actual method and its source identity; they require deliberate path rebinding, not blind execution.
