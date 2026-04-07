# Tables — ORM Models

Current SQLAlchemy models in `db/models.py`.

## Project

Stores project identity and repository configuration.

| Field | Type | Notes |
|---|---|---|
| `project_id` | Integer PK | Auto-increment |
| `name` | String | Project display name |
| `repo_path` | String | Local path to the repository |
| `remote_repo_url` | String | Remote git URL |
| `branch` | String | Active branch |
| `branches` | JSON | Known branches list |
| `key_path` / `ssh_key` | String | SSH key path for git access |
| `public_key` | String | Deployed SSH public key |

## Message

Stores ordered project execution message artifacts.

| Field | Type | Notes |
|---|---|---|
| `message_id` | Integer PK | Auto-increment |
| `project_id` | FK → Project | Scoped to one project |
| `sequence_no` | Integer | Ordered sequence within project |
| `role` | String | `user`, `assistant`, `tool` |
| `content` | Text | Message content |
| `ai_model_name` | String | Model used for this artifact |
| `tool_call_id` | String | Tool call reference if applicable |
| `tool_calls` | JSON | Tool calls metadata |
| `created_at` | DateTime | Row creation time |

## File

Stores project-scoped file snapshot rows (persistence-backed, not live reads).

| Field | Type | Notes |
|---|---|---|
| `file_id` | Integer PK | Auto-increment |
| `project_id` | FK → Project | Scoped to one project |
| `relative_repo_path` | String | Repo-relative path |
| `name` | String | Filename |
| `content` | Text | Snapshot content |
| `total_lines` | Integer | Total line count |
| `created_at` | DateTime | Snapshot time |

## Note

`FilesRepository` and `MessagesRepository` serve these models at the persistence layer. Higher-level access goes through `FileRuntime` and `MessageRuntime` functions respectively.
