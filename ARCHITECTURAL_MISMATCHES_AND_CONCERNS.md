# Architectural Mismatches and Concerns

_This document is a gap/deprecation register._

_It exists to track what is still wrong, missing, deprecated, or architecturally risky for MVP alignment._

_It is **not** a map of implemented features, and it should not retain solved items except where a solved item still creates an active deprecation risk above it._

## Purpose

Use this file to keep three things explicit:

- unresolved architectural gaps
- active deprecations that still matter
- missing functionality or missing adoption that still blocks clean MVP behavior

## Source-of-Truth Rule

For this file:

- documented intended ownership remains the source of truth
- current code is only evidence of remaining gaps or drift
- once a gap is actually implemented and no longer creates an active blocker, it should be removed from this file

## MVP-Critical Active Gaps and Deprecations

At the moment, no active backend ownership gaps remain in this register.

The project now hardens this directly by:

- failing explicit misuse on deprecated lower owners such as `FilesRepository`, `MessagesRepository`, and `RepositoryRuntime`
- requiring explicit `BoundProjectRuntime.require_*_runtime()` access instead of direct runtime attribute grabs
- narrowing route-facing runtime helpers to the intended `FileRuntime` and `MessageRuntime` surfaces

## Bottom Line

What remains here should be read as:

- unresolved gap
- active deprecation
- missing route/backend convergence

What has already been implemented should be removed from this file unless it still creates an active unresolved risk above it.
