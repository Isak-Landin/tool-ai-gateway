import os
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:4100").rstrip("/")
BRIDGE_HOST = os.getenv("BRIDGE_HOST", "0.0.0.0")
BRIDGE_PORT = int(os.getenv("BRIDGE_PORT", "4110"))
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", "200000"))

PROJECT_ROOT_ENV_KEYS = [key for key in os.environ.keys() if key.startswith("PROJECT_ROOT_")]
PROJECT_ROOTS = {
    key: Path(os.environ[key]).resolve()
    for key in sorted(PROJECT_ROOT_ENV_KEYS)
    if os.environ.get(key, "").strip()
}


def is_subpath(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def get_root_by_name(root_name: str):
    return PROJECT_ROOTS.get(root_name)


def safe_join(root: Path, relative_path: str) -> Path | None:
    candidate = (root / relative_path).resolve()
    if not is_subpath(candidate, root):
        return None
    return candidate


def build_tree(base: Path, current: Path):
    items = []
    try:
        children = sorted(
            current.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower())
        )
    except Exception:
        return items

    for child in children:
        print(child)
        rel_path = str(child.relative_to(base))
        node = {
            "name": child.name,
            "path": rel_path,
            "type": "directory" if child.is_dir() else "file",
        }
        if child.is_dir():
            node["children"] = build_tree(base, child)
        items.append(node)

    return items


@app.route("/")
def index():
    return render_template(
        "index.html",
        gateway_base_url=GATEWAY_BASE_URL,
        roots=list(PROJECT_ROOTS.keys()),
    )


@app.route("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "gateway_base_url": GATEWAY_BASE_URL,
            "roots": list(PROJECT_ROOTS.keys()),
        }
    )


@app.route("/api/tree", methods=["GET"])
def api_tree():
    response = {}

    for root_name, root_path in PROJECT_ROOTS.items():
        if root_path.exists() and root_path.is_dir():
            response[root_name] = {
                "root_path": str(root_path),
                "children": build_tree(root_path, root_path),
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

    file_path = safe_join(root, rel_path)
    if not file_path:
        return jsonify({"ok": False, "error": "invalid_path"}), 400

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

    try:
        gateway_response = requests.post(
            f"{GATEWAY_BASE_URL}/chat",
            json=payload,
            timeout=120,
        )
        gateway_response.raise_for_status()
    except requests.RequestException as exc:
        return jsonify(
            {
                "ok": False,
                "error": "gateway_request_failed",
                "details": str(exc),
            }
        ), 502

    try:
        response_json = gateway_response.json()
    except ValueError:
        return jsonify(
            {
                "ok": False,
                "error": "gateway_non_json_response",
                "status_code": gateway_response.status_code,
                "raw_text": gateway_response.text,
            }
        ), 502

    return jsonify({"ok": True, "gateway_response": response_json})


if __name__ == "__main__":
    app.run(host=BRIDGE_HOST, port=BRIDGE_PORT, debug=False)
