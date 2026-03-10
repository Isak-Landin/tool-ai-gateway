import os
from pathlib import Path

import pathspec
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="templates", static_folder="static")

GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:4100").rstrip("/")
BRIDGE_HOST = os.getenv("BRIDGE_HOST", "0.0.0.0")
BRIDGE_PORT = int(os.getenv("BRIDGE_PORT", "4110"))
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", "200000"))

CONTAINER_PROJECTS_BASE = Path(os.getenv("CONTAINER_PROJECTS_BASE", "/app")).resolve()

DEFAULT_IGNORE_NAMES = {"venv", ".git", ".idea"}
EXTRA_IGNORE_NAMES = {
    item.strip()
    for item in os.getenv("IGNORE_NAMES", "").split(",")
    if item.strip()
}
FORCED_IGNORE_NAMES = DEFAULT_IGNORE_NAMES | EXTRA_IGNORE_NAMES

PROJECT_CONFIGS = {}
for key, value in os.environ.items():
    if not key.startswith("PROJECT_NAME_"):
        continue

    suffix = key.removeprefix("PROJECT_NAME_")
    project_name = value.strip()
    if not project_name:
        continue

    project_root = (CONTAINER_PROJECTS_BASE / project_name).resolve()
    PROJECT_CONFIGS[project_name] = {
        "name": project_name,
        "root": project_root,
    }


def is_subpath(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def get_root_by_name(root_name: str):
    config = PROJECT_CONFIGS.get(root_name)
    if not config:
        return None
    return config["root"]


def safe_join(root: Path, relative_path: str) -> Path | None:
    candidate = (root / relative_path).resolve()
    if not is_subpath(candidate, root):
        return None
    return candidate


def load_ignore_spec(root: Path):
    patterns = []

    gitignore_path = root / ".gitignore"
    if gitignore_path.exists() and gitignore_path.is_file():
        try:
            lines = gitignore_path.read_text(encoding="utf-8").splitlines()
            patterns.extend(lines)
        except Exception:
            pass

    for name in sorted(FORCED_IGNORE_NAMES):
        patterns.append(name)
        patterns.append(f"{name}/")
        patterns.append(f"**/{name}")
        patterns.append(f"**/{name}/")

    # hide .env file by default unless explicitly wanted
    patterns.extend([
        ".env",
        "**/.env",
    ])

    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def should_ignore(root: Path, path: Path, ignore_spec) -> bool:
    try:
        rel_path = path.relative_to(root).as_posix()
    except ValueError:
        return True

    if not rel_path:
        return False

    if path.name in FORCED_IGNORE_NAMES:
        return True

    match_path = rel_path + "/" if path.is_dir() else rel_path
    return ignore_spec.match_file(match_path)


def build_tree(base: Path, current: Path, ignore_spec):
    items = []

    try:
        children = sorted(
            current.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower())
        )
    except Exception:
        return items

    for child in children:
        if should_ignore(base, child, ignore_spec):
            continue

        rel_path = child.relative_to(base).as_posix()

        node = {
            "name": child.name,
            "path": rel_path,
            "type": "directory" if child.is_dir() else "file",
        }

        if child.is_dir():
            node["children"] = build_tree(base, child, ignore_spec)

        items.append(node)

    return items


@app.route("/")
def index():
    return render_template(
        "index.html",
        gateway_base_url=GATEWAY_BASE_URL,
        roots=list(PROJECT_CONFIGS.keys()),
    )


@app.route("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "gateway_base_url": GATEWAY_BASE_URL,
            "roots": list(PROJECT_CONFIGS.keys()),
        }
    )


@app.route("/api/tree", methods=["GET"])
def api_tree():
    response = {}

    for root_name, config in PROJECT_CONFIGS.items():
        root_path = config["root"]

        if root_path.exists() and root_path.is_dir():
            ignore_spec = load_ignore_spec(root_path)
            response[root_name] = {
                "root_path": str(root_path),
                "children": build_tree(root_path, root_path, ignore_spec),
            }
        else:
            response[root_name] = {
                "root_path": str(root_path),
                "children": [],
                "error": "root_not_found",
            }

    return jsonify({"ok": True, "roots": response})


@app.route("/api/read", methods=["POST"])
def api_read():
    data = request.get_json(silent=True) or {}

    root_name = data.get("root")
    rel_path = data.get("path")

    if not root_name or not rel_path:
        return jsonify({"ok": False, "error": "root_and_path_required"}), 400

    root = get_root_by_name(root_name)
    if not root:
        return jsonify({"ok": False, "error": "invalid_root"}), 400

    ignore_spec = load_ignore_spec(root)

    file_path = safe_join(root, rel_path)
    if not file_path:
        return jsonify({"ok": False, "error": "invalid_path"}), 400

    if should_ignore(root, file_path, ignore_spec):
        return jsonify({"ok": False, "error": "path_ignored"}), 403

    if not file_path.exists() or not file_path.is_file():
        return jsonify({"ok": False, "error": "file_not_found"}), 404

    size = file_path.stat().st_size
    if size > MAX_FILE_BYTES:
        return jsonify(
            {
                "ok": False,
                "error": "file_too_large",
                "max_file_bytes": MAX_FILE_BYTES,
                "actual_file_bytes": size,
            }
        ), 400

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return jsonify({"ok": False, "error": "file_not_utf8"}), 400

    return jsonify(
        {
            "ok": True,
            "root": root_name,
            "path": rel_path,
            "content": content,
            "size": size,
        }
    )


@app.route("/api/send-to-gateway", methods=["POST"])
def api_send_to_gateway():
    data = request.get_json(silent=True) or {}

    files = data.get("files", [])
    instruction = data.get("instruction", "")

    if not isinstance(files, list):
        return jsonify({"ok": False, "error": "files_must_be_list"}), 400

    payload = {
        "message": instruction,
        "context_files": files,
    }
    gateway_response = None
    try:
        gateway_response = requests.post(
            f"{GATEWAY_BASE_URL}/chat",
            json=payload,
            timeout=120,
        )
    except requests.RequestException as exc:
        print(str(exc))
        return jsonify(
            {
                "ok": False,
                "error": "gateway_request_failed",
                "details": str(exc),
            }
        ), gateway_response.status_code if gateway_response else 502

    try:
        response_json = gateway_response.json()
    except ValueError as exc:
        print(str(exc))
        return jsonify(
            {
                "ok": False,
                "error": "gateway_non_json_response",
                "status_code": gateway_response.status_code,
                "raw_text": gateway_response.text,
            }
        ), gateway_response.status_code if gateway_response else 502

    return jsonify({"ok": True, "gateway_response": response_json})


if __name__ == "__main__":
    app.run(host=BRIDGE_HOST, port=BRIDGE_PORT, debug=False)