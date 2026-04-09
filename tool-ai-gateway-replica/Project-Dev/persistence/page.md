# persistence

_Idea development tracking for the persistence module._

---

# Confirmed

## API

## BoundProjectRuntime

## db

## execution

## FileRuntime

## MessageRuntime

## ollama

## ProjectResolver

## ProjectRuntimeBinder

## repository_runtime

## repository_tools

## ui

## web_search

---

# Being Developed

## API

## BoundProjectRuntime

## db

## execution

## FileRuntime

## MessageRuntime

## ollama

## ProjectResolver

## ProjectRuntimeBinder

## repository_runtime

**BS1 verification responder**

A persistence-layer method that receives the BS1 failure enum and decides what action to take. Performs its own DB and disk checks before any decision — does not rely on the BS layer to report state beyond the initial failure enum.

Non-skippable preconditions checked by persistence before acting:
- DB: does the project row exist? Are BS1 fields (`repo_path`, `ssh_key`, `public_key_path`) populated or absent?
- Disk: does the project directory exist? SSH directory? Key files present?

Cases mapped so far:
- **Case A** — project row exists, BS1 fields absent, no disk artifacts. First project-entry visit after creation. Persistence runs BS1 directly without further checks.
- **Case B** — project row exists, BS1 fields partially present, disk partially present, no message or repo-change history in DB. Persistence cleans up partial DB fields and disk artifacts, then re-runs BS1.

More cases exist but are not yet mapped.

---

**BS2 verification responder**

A persistence-layer method that receives the BS2 failure enum and decides what action to take. More complex than the BS1 responder because it must handle states where the repository has never been cloned, was partially cloned, and where clone succeeded previously but something changed.

Non-skippable preconditions checked by persistence before acting — these differ from BS1 because BS2 has the right to expect BS1 to be complete:
- DB: project row exists? All three BS1 fields populated (`repo_path`, `ssh_key`, `public_key_path`)? If not, wrong call state entirely.
- Disk: does `repo_path` exist as a directory? Is it a git repository?

Cases per failure enum:
- **NOT_GIT_REPO / repo dir missing** — never cloned. Persistence runs BS2 directly.
- **NOT_GIT_REPO / repo dir present but not a git repo** — interrupted clone. Persistence cleans disk, then runs BS2.
- **ORIGIN_REMOTE_URL_MISMATCH** — valid git repo exists but origin doesn't match `remote_repo_url` in DB. Config divergence. Not yet fully mapped.
- **ORIGIN_REMOTE_UNREACHABLE** — repo exists, origin matches, SSH cannot reach remote. Persistence cannot auto-resolve. User must correct SSH key setup. Surfaces bootstrap guidance.

Operational runtime states (broken repo, needs merge, stale) that emerge after a successful BS2 are expected to belong to a separate surface outside bootstrap. These are not BS2 verification failures and are not mapped here.

## repository_tools

## ui

## web_search

---

# Uncertain

## API

## BoundProjectRuntime

## db

## execution

## FileRuntime

## MessageRuntime

## ollama

## ProjectResolver

## ProjectRuntimeBinder

## repository_runtime

## repository_tools

## ui

## web_search
