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

**BS responder pre-call rule — declared**

Both the BS1 and BS2 persistence responders will always perform their persistence-level checks (DB and disk) before proceeding to call `bs1(...)` or `bs2(...)`. This is unconditional. There are no code paths in either responder where bs1 or bs2 is called without the persistence checks having run first.

This is declared here to eliminate any ambiguous interpretation later. The checks are not optional, not skippable under any case, and not the responsibility of the BS layer to perform. The persistence responder is the authoritative decision point — calling into BS without first establishing current state would make the responder a blind executor, which is not its role.

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

More cases exist but are not yet mapped. And are not intended to be included in MVP unless absolutely essential for a functional MVP.

---

**BS2 verification responder**

A persistence-layer method that receives the BS2 failure enum and decides what action to take. More complex than the BS1 responder because it must handle states where the repository has never been cloned, was partially cloned, and where clone succeeded previously but something changed.

The precondition scope for BS2 is broader than BS2 alone. Since BS2 success is entirely dependent on BS1 completion, the persistence responder is not limited to ensuring BS2-related steps are in place — it must verify that all BS1 preconditions are also met. Performing only BS2-scoped checks would leave BS1-originated preconditions unverified and produce runtime errors outside the expected error surface.

Non-skippable preconditions checked by persistence before acting — these differ from BS1 because BS2 has the right to expect BS1 to be complete:
- DB: project row exists? All three BS1 fields populated (`repo_path`, `ssh_key`, `public_key_path`)? If not, wrong call state entirely.
- Disk: does `repo_path` exist as a directory? Is it a git repository? Must also ensure `ssh_key` representation exists, as disk represented file, not only db row.

Cases per failure enum:
- **NOT_GIT_REPO / repo dir missing** — never cloned. Persistence runs BS2 directly.
- **NOT_GIT_REPO / repo dir present but not a git repo** — interrupted clone. Persistence cleans disk, then runs BS2.
- **ORIGIN_REMOTE_URL_MISMATCH** — valid git repo exists but origin doesn't match `remote_repo_url` in DB. Config divergence. Not yet fully mapped.
- **ORIGIN_REMOTE_UNREACHABLE** — repo exists, origin matches, SSH cannot reach remote. Persistence cannot auto-resolve. User must correct SSH key setup. Surfaces bootstrap guidance.

Operational runtime states (broken repo, needs merge, stale) that emerge after a successful BS2 are expected to belong to a separate surface outside bootstrap. These are not BS2 verification failures and are not mapped here.

The absence of a mapped action case for a given error does not mean the general checks for that state are also absent. Persistence is still fully responsible for ensuring no BS-related precondition is missed — even for errors where no active recovery is performed.

More rules are not mapped. The exclusion of more is not yet determined. We are not finished mapping all relating **routes**, **if no more** certain use cases are determined, we will move on with the **four pre determined cases**.

**BS1 AND BS2:**

Very important to understand is that the mapping of checks and all other agile idea development does not make any declarations of ownership. It does not declare from which module a check is imported or partially derived. The only truth in checks and all other Project Dev documentation that can be derived, always, is the effective intention, functionality and result from a end consumer perspective.

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

We are expected to call bs from the persistence level. However, it is **not determined** if we are allowed, supposed to or expected to make **use** of any **other repository runtime modules**. The main concern is for shell. Since shell is passed around as an instantiated object which is expected to persist and be reused throughout application workflow, it is extremely unlikely that we expect initiation in persistence level. We should if developed as intended, neither expect shell direct method usage.

For **git** direct calling, we **cannot apply** any certain **rules** yet. We have a lot of **checks** which **relate to git** specific actions. Even if we perform no direct shell method calls, we will still need shell passed for both bs and git, they in turn may or may not utilize shell specific method calls directly without direct involvement from persistence level calling. It is extremely likely that we will expect direct git function usage from persistence level for bs related checks.

## repository_tools

## ui

## web_search
