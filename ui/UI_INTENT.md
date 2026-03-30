# UI Intent Map

_This document defines the intended UI direction for the product surface._

_It is UI planning, not a backend contract._

_When UI assumptions conflict with stabilized lower-layer behavior, the lower layers should win and the UI intent should be updated._

## Purpose

The UI should present one coherent project-centered product surface for:

- entering the system
- seeing what projects exist
- creating a project
- working inside one project workspace
- reading files and repository structure
- reading AI/chat history
- sending new project-scoped requests

## Current Intent Priority

The current priority is not broad user-account coverage.

The current priority is:

- project collection flow
- project creation flow
- primary project workspace
- project history visibility
- project settings only where they are truly project-scoped

User/account/auth surfaces can still exist in planning, but they are not the current source of MVP shape.

## Core Product Shape

The product should feel:

- project-centered
- technical but calm
- stable across pages
- closer to a workspace than to a collection of utility screens

The UI should communicate that the project page is where real work happens.

## Navigation Model

### Product-level navigation

Primary destinations that matter right now:

- Home
- Projects
- New Project

Future or lower-priority destinations:

- Account
- Settings
- Login / Logout

### Project-level navigation

Primary project destinations:

- Workspace
- Activity
- Settings

The project workspace remains the main working page.

## Current MVP Route Direction

### Public MVP route

- `/`

### Project collection MVP routes

- `/projects`
- `/projects/new`

### Project MVP routes

- `/projects/<project_id>`
- `/projects/<project_id>/activity`
- `/projects/<project_id>/settings`

### Support routes

- `/403`
- `/404`
- `/503`

## Page Roles

### Landing / Home

Role:

- explain the product simply
- route the user toward projects
- visually prepare the user for the workspace

### Projects List

Role:

- show project collection at a glance
- act as the default signed-in entry into actual work

### Create Project

Role:

- handle project bootstrap as a dedicated setup step
- stay visually separate from the day-to-day workspace

### Project Workspace

Role:

- be the primary project interaction page
- combine repository navigation, file reading, AI/chat history, and request submission

### Project Activity

Role:

- show ordered message/history activity and notable execution events

### Project Settings

Role:

- hold actual project-scoped configuration only
- avoid polluting the main workspace with rare controls

## Workspace Composition

The project workspace should be organized around three major regions:

- repository tree
- central presenter
- chat/input region

These are the main structural anchors.

## Repository Tree Region

Intent:

- show repository-root structure
- prioritize orientation and safety
- allow controlled directory expansion

Rules:

- start from repository root, not broader project storage
- root-level files should be visible immediately
- directories should default closed
- the tree should not start in an empty-looking state
- the project container itself should not appear as an extra parent layer

## Central Presenter Region

Intent:

- be the dominant reading surface
- support real file reading
- support real conversation/history reading

The central presenter should support local no-reload toggling between:

- file content mode
- AI/chat history mode

### File content mode

Shows:

- currently selected file
- readable file content
- file-oriented title information

### AI/chat history mode

Shows:

- chat history
- assistant responses
- model thoughts

Model thoughts belong with AI/chat history, not in a separate unrelated area.

## Chat/Input Region

Intent:

- anchor the active user request flow
- stay wide enough for real prompts
- stay integrated with the workspace rather than becoming a detached page

The input area should support:

- prompt input
- send action
- branch selection
- model selection
- room for future adjacent controls

The large history-reading surface belongs in the central presenter, not in the input region.

## Model Selection Direction

The UI must no longer treat the project itself as owning one persistent selected model.

That older assumption is deprecated.

### Current intended model behavior

- model choice is a workspace/run-time concern
- the project record should not be the owner of selected model state
- the model actually used for a response should be archived on message artifacts through `messages.ai_model_name`

### What this means for the UI

- the workspace may present a model dropdown
- changing the selected model should affect future runs, not rewrite project metadata
- previously generated responses should still show which model produced them through message history data

### MVP sourcing of model options

For current MVP simplicity:

- the UI may provide a static model-option list inside the UI layer

Later, the cleaner long-term direction is:

- a separate non-persistence-backed backend route such as `/models`
- that route should represent live backend model availability rather than database-stored values

That route is part of the intended direction, but not required to be implemented right now.

## Branch Selection Direction

Branch remains more project/runtime-adjacent than model selection.

Current intent:

- the project may still have a default branch
- the workspace may allow branch override for runs
- branch selection belongs in workspace controls because it affects repository-scoped work

## Message and History Direction

Message processing is required MVP behavior, not optional polish.

The UI should assume:

- project history matters
- message persistence matters
- assistant outputs and tool artifacts form an ordered project history
- the actual `ai_model_name` used for a response belongs in message history
- execution owns bounded recent-history use during runs
- route/shared history views should rely on a project-scoped message-serving surface rather than execution-only persistence paths

This supports:

- project activity view
- AI/chat history mode in the workspace
- future auditability of which model produced which response

## Project Settings Direction

Project settings should only include fields that are truly project-scoped.

Reasonable project-scoped fields:

- project name
- default branch

Not intended as project-scoped settings:

- a permanent project-owned selected model

## Theme and Shell Direction

The UI should keep:

- one global theme language
- one stable public shell
- one stable app shell
- one stable project shell

The workspace should feel IDE-adjacent in structure, but should not copy a specific editor literally.

## MVP Expectations

The MVP UI should already assume:

- repository navigation is real
- file reading is real
- message history is real
- message persistence is real
- execution is project-scoped
- the workspace is the primary product surface

The MVP UI should not assume:

- placeholder project status fields are backend truth
- hardcoded tree/file/history data is backend truth
- project metadata owns current model selection

## Future Expansion

The final product can still extend the same UI system with:

- auth flows
- richer project collection views
- collaboration views
- account and security pages
- richer activity timelines
- deeper context-management surfaces
- live model availability discovery

The important thing is that these should extend the same workspace-centered system rather than replace it.

## References

This UI direction is primarily shaped by:

- `LAYER_INTENT.md`
- `LAYER_RULES.md`
- `execution/runtime_execution.md`
- current backend data and lower-layer ownership

This file intentionally follows those sources instead of treating placeholder UI code as truth.
