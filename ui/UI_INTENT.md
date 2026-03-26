# UI Intent Map

_This document is a visual and navigational planning document for the UI only._

_It does not define backend contracts, response shapes, persistence details, or execution behavior._

## Purpose

The UI should present one coherent product surface for:

- entering the system
- understanding what projects exist
- moving into one project workspace
- asking questions and reading responses
- managing project-level setup and configuration
- handling account access and future user-bound ownership cleanly

The goal is not to preserve current pages as the final structure.  
The goal is to define the page system the UI should grow toward while keeping one consistent visual language.

## Design Direction

The UI should feel like:

- a focused project workspace
- calm, readable, and tool-oriented
- capable of supporting both a narrow MVP and a broader final product

The design language should prioritize:

- clear hierarchy
- strong spacing rhythm
- durable workspace layouts
- restrained color usage
- obvious navigation
- predictable page shells

## Theme System

### Core visual character

The theme should be:

- dark-aware or dark-first in feeling, even if light mode remains available
- minimal rather than decorative
- technical without looking raw or unfinished
- consistent across auth, dashboard, project, and settings pages

### Visual principles

- one global app shell
- one consistent typography system
- one spacing system
- one card system
- one form system
- one status color system
- one interaction language for buttons, tabs, sidebars, and panels

### Primary surfaces

The UI should rely on a small set of repeated surfaces:

- app background
- top navigation
- left project/workspace navigation
- content canvas
- cards
- panels
- tables/lists
- forms
- message/thread surfaces
- modal/drawer surfaces

### Interaction states

Every page family should support a consistent treatment for:

- default
- hover
- active
- selected
- disabled
- loading
- empty
- success
- warning
- error

## Global Navigation Model

The UI should eventually have two navigation levels.

### 1. Product-level navigation

Used before entering a specific project and when moving between major product areas.

Main destinations:

- Home
- Projects
- New Project
- Account
- Settings
- Login / Logout

### 2. Project-level navigation

Used after entering a specific project workspace.

Main destinations:

- Workspace
- Activity
- Settings

## Page Families

The UI should be planned as page families, not only isolated pages.

### A. Entry and auth pages

These pages establish product access and user identity.

Planned pages:

- Landing / Home
- Login
- Register
- Forgot Password
- Reset Password
- Invitation / Accept Access

Intent:

- explain the product simply
- provide clean access entry
- separate public entry from signed-in workspace pages

### B. Project collection pages

These pages show project ownership and project discovery.

Planned pages:

- My Projects
- Shared With Me
- Archived Projects
- Create Project
- Project Bootstrap Complete

Intent:

- make user-bound project organization obvious
- support ownership and collaboration later without redesigning the whole shell
- keep project creation visually separate from project work

### C. Project workspace pages

These pages are the core signed-in product experience.

Planned pages:

- Project Workspace
- Project Activity / History
- Project Settings

Intent:

- provide one stable workspace shell
- let the user stay oriented inside one project
- allow future growth without changing the basic navigation model
- keep the most important project work in one integrated screen rather than splitting it too early

### D. Account and user pages

These pages handle user-level identity and preferences.

Planned pages:

- Account Overview
- Profile
- User Preferences
- Security

Intent:

- keep personal settings separate from project settings
- make future user-bound project ownership feel native

### E. System and support pages

These pages support app-wide UX consistency.

Planned pages:

- Not Found
- Access Denied
- Service Unavailable
- Empty State Variants

Intent:

- make failure states feel designed, not accidental
- preserve the same shell and tone across edge cases

## Route and Page Map

This map is intentionally UI-facing only.

### Public routes

- `/`
- `/login`
- `/register`
- `/forgot-password`
- `/reset-password`

### Authenticated top-level routes

- `/home`
- `/projects`
- `/projects/new`
- `/projects/shared`
- `/projects/archived`
- `/account`
- `/settings`

### Project workspace routes

- `/projects/<project_id>`
- `/projects/<project_id>/activity`
- `/projects/<project_id>/settings`

### Support routes

- `/403`
- `/404`
- `/503`

## Recommended Shell Structure

### Public shell

Used for landing and auth pages.

Visual structure:

- simplified top bar
- centered content
- strong headline area
- minimal distractions

### App shell

Used for signed-in top-level pages like project lists and account pages.

Visual structure:

- persistent top navigation
- optional secondary navigation
- page title area
- content grid or list area

### Project workspace shell

Used for all project subpages.

Visual structure:

- persistent top navigation
- persistent project sidebar
- project title/status strip
- main work canvas
- optional right-side contextual panel

This shell should remain stable even as individual project subpages change.

## Primary Project Workspace

The default project page should be the main project workspace.

It should not be treated as a thin landing page that immediately pushes the user into many separate pages for normal work.

The project page is meant to hold the most important working surfaces together in one layout.

### Core workspace composition

The main project workspace should be organized around three major regions:

- repository tree
- central presenter
- chat area

These are not the only possible sections in the final interface, but they are the primary visual structure.

### 1. Repository tree region

Intent:

- present the repository as a navigable file tree
- prioritize orientation and safety
- allow directory expansion on demand

Rules:

- the tree starts from the repository root, not the broader project directory
- root-level repository files should be visible immediately
- directories should default to closed
- the default closed state should still avoid an empty-looking tree
- the project container itself should not appear as an extra collapsed parent layer

Reasoning:

- users should see real repository files immediately
- the tree should feel useful on first load
- the UI should not visually encourage navigation into non-repository project storage

Visual behavior:

- tall but relatively narrow
- optimized for scanning
- supports expandable directories
- supports clear selected-file state

### 2. Central presenter region

Intent:

- act as the main large reading surface in the workspace
- give enough width for real code, text, and conversation reading
- remain the dominant content pane

Visual behavior:

- larger than the repository tree
- both wide and tall
- suited for long-form file reading and long-form conversation reading
- able to host tabs, file title bars, and future inline utilities if needed

This region should feel closer to a primary workspace presenter than a small preview panel.

### Presenter modes

The central presenter should support local no-reload toggling between:

- file content mode
- AI/chat history mode

This should be a direct workspace toggle, not a full page navigation pattern.

Suggested visual direction:

- one file-oriented toggle icon
- one AI/chat-oriented toggle icon
- quick switching between views inside the same presenter container

### File content mode

In file content mode, the central presenter shows:

- the currently selected file
- readable file content
- file-oriented title or tab affordances

### AI/chat history mode

In AI/chat history mode, the same central presenter shows:

- chat history
- AI responses
- model thoughts

Model thought presentation should belong with the chat experience, not in a separate unrelated page area.

The thought view should therefore live inside the AI/chat mode of the central presenter.

### 3. Chat region

Intent:

- provide the main user-to-system interaction surface
- anchor the active input controls for the chat experience
- allow relatively long prompts without feeling cramped
- coexist with repository navigation and file reading in the same workspace

Visual behavior:

- wide enough for comfortable writing
- short compared with the file presenter, but not so short that longer prompts become frustrating
- tall enough to support real prompt writing without hiding the text too early

The chat input area should visually support:

- message input
- send action
- branch selection dropdown
- model selection dropdown
- room for future adjacent controls

The chat history itself should not compete with the file tree for space in a separate main region.

Instead:

- the input and control surface remain in the chat region
- the larger chat history and model thought reading surface live in the central presenter when AI/chat mode is active

## Workspace Layout Direction

The project workspace should feel closer to an IDE-inspired environment than a sequence of separate utility pages.

The intended layout direction is:

- narrow repository navigation on one side
- dominant toggleable presenter in the middle
- integrated chat input area as a major workspace section

This does not require copying any existing editor literally.  
It means the workspace should prioritize simultaneous visibility of:

- repository structure
- the currently selected file or AI/chat history
- the current input and conversation controls

## Project Page Role

`/projects/<project_id>` should be the primary working page for a project.

It should combine:

- repository navigation
- file viewing
- AI/chat history viewing
- chat interaction
- project-scoped controls

It should not be treated as a temporary overview page that exists only to link outward to the “real” pages.

## Secondary Project Pages

The project should still be allowed to have additional pages when they serve distinct secondary roles.

Recommended secondary pages:

- `/projects/<project_id>/activity`
- `/projects/<project_id>/settings`

Optional future secondary pages may exist, but the core repository/file/chat experience should remain centered on the primary workspace page.

## Recommended Page Roles

### Landing / Home

Role:

- present the product clearly
- route people to login or project work

### Projects

Role:

- show project collection at a glance
- become the default signed-in home

### Create Project

Role:

- handle project setup as a focused creation flow
- feel separate from the main workspace

### Project Workspace

Role:

- be the primary interaction surface for a project
- combine repository tree, central toggleable presenter, and chat input/control area in one coherent workspace
- become the visual center of the MVP and remain valid in the final product

### Project Activity

Role:

- present history and notable workspace events in one readable timeline-oriented page

### Project Settings

Role:

- hold project-specific controls without polluting the main work pages

## MVP Page Set

The MVP UI can stay narrow while still matching the final structure direction.

Recommended MVP page set:

- Landing or Projects Home
- Login
- Projects List
- Create Project
- Project Workspace
- Project Settings
- Designed error pages

This gives MVP a real product shape without needing every future page immediately.

## Final Product Expansion

The final UI can extend the same page map with:

- registration and invitation flows
- shared-project views
- archived-project views
- richer account/security surfaces
- project activity timelines
- more advanced context-management pages
- deeper repository workspace panels

The important thing is that these should feel like natural additions to the same system, not a redesign.

## Current UI vs Intended UI

Current visible surfaces are still very small:

- project list
- create project
- project detail
- error page

These should be treated as early fragments of a larger page family system.

The intended next UI direction is not “add one-off pages.”  
It is:

- establish the theme
- establish the page families
- establish the shell system
- then implement pages inside that structure

## References That Shaped This Direction

This UI mapping was shaped by the broader project intent:

- `README.md`
- `LAYER_INTENT.md`
- `LAYER_RULES.md`
- `execution/runtime_execution.md`
- `ollama/ollama_architecture_intent.md`

Those documents suggest:

- MVP should stay focused and reliable
- the product is project-centered
- execution remains project-scoped and iterative
- the UI must support both narrow MVP use and a broader final workspace model
- the primary project experience should keep repository structure, file reading, AI/chat history, and chat controls together on one main page

This UI document translates that into page structure and theme direction only.
