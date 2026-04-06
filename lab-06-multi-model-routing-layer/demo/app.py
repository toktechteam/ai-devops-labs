import json
import os
import urllib.error
import urllib.request
from typing import Optional, Tuple

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

DEFAULT_INGEST_URL = os.environ.get("INGEST_API_URL", "")
DEFAULT_ROUTE_URL = os.environ.get("ROUTE_API_URL", "")
DEFAULT_AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")


def _post_json(api_url: str, token: str, payload: dict) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"error": body}
    except Exception as exc:  # noqa: BLE001
        return 500, {"error": str(exc)}


def _parse_json_field(raw_value: object) -> Tuple[bool, Optional[dict], Optional[str]]:
    if raw_value is None:
        return True, None, None
    if isinstance(raw_value, dict):
        return True, raw_value, None
    if isinstance(raw_value, str):
        cleaned = raw_value.strip()
        if not cleaned:
            return True, None, None
        try:
            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                return False, None, "Must be a JSON object"
            return True, parsed, None
        except json.JSONDecodeError:
            return False, None, "Invalid JSON"
    return False, None, "Invalid JSON"


@app.route("/")
def index():
    return render_template(
        "index.html",
        default_ingest_url=DEFAULT_INGEST_URL,
        default_route_url=DEFAULT_ROUTE_URL,
        default_auth_token=DEFAULT_AUTH_TOKEN,
    )


@app.route("/api/ingest", methods=["POST"])
def ingest():
    data = request.get_json(silent=True) or {}
    api_url = data.get("ingest_url") or DEFAULT_INGEST_URL
    token = data.get("auth_token") or DEFAULT_AUTH_TOKEN

    if not api_url:
        return jsonify({"error": "Ingest URL is required"}), 400

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Text is required"}), 400

    ok, metadata, error = _parse_json_field(data.get("metadata"))
    if not ok:
        return jsonify({"error": f"Metadata JSON error: {error}"}), 400

    payload = {
        "doc_id": data.get("doc_id") or "routing-doc",
        "text": text,
        "chunk_size": int(data.get("chunk_size") or 800),
        "chunk_overlap": int(data.get("chunk_overlap") or 120),
    }
    if metadata:
        payload["metadata"] = metadata

    status, response = _post_json(api_url, token, payload)
    return jsonify({"status": status, "payload": response})


@app.route("/api/route", methods=["POST"])
def route():
    data = request.get_json(silent=True) or {}
    api_url = data.get("route_url") or DEFAULT_ROUTE_URL
    token = data.get("auth_token") or DEFAULT_AUTH_TOKEN

    if not api_url:
        return jsonify({"error": "Route URL is required"}), 400

    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    ok, filters, error = _parse_json_field(data.get("filters"))
    if not ok:
        return jsonify({"error": f"Filters JSON error: {error}"}), 400

    payload = {
        "prompt": prompt,
        "task_type": (data.get("task_type") or "").strip() or None,
        "top_k": int(data.get("top_k") or 5),
        "temperature": float(data.get("temperature") or 0.2),
        "force_rag": bool(data.get("force_rag")),
    }

    model_override = (data.get("model_override") or "").strip()
    if model_override:
        payload["model_override"] = model_override

    if filters:
        payload["filters"] = filters

    status, response = _post_json(api_url, token, payload)
    return jsonify({"status": status, "payload": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)
