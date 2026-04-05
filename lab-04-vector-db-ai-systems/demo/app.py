import json
import os
import urllib.error
import urllib.request

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

DEFAULT_INGEST_URL = os.environ.get("INGEST_API_URL", "")
DEFAULT_SEARCH_URL = os.environ.get("SEARCH_API_URL", "")
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
        with urllib.request.urlopen(req, timeout=60) as resp:
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


@app.route("/")
def index():
    return render_template(
        "index.html",
        default_ingest_url=DEFAULT_INGEST_URL,
        default_search_url=DEFAULT_SEARCH_URL,
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

    payload = {
        "doc_id": data.get("doc_id") or "sample-doc",
        "text": text,
        "chunk_size": data.get("chunk_size") or 800,
        "chunk_overlap": data.get("chunk_overlap") or 100,
    }

    status, response = _post_json(api_url, token, payload)
    return jsonify({"status": status, "payload": response})


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    api_url = data.get("search_url") or DEFAULT_SEARCH_URL
    token = data.get("auth_token") or DEFAULT_AUTH_TOKEN

    if not api_url:
        return jsonify({"error": "Search URL is required"}), 400

    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Query is required"}), 400

    payload = {
        "query": query,
        "top_k": int(data.get("top_k") or 5),
    }

    status, response = _post_json(api_url, token, payload)
    return jsonify({"status": status, "payload": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)
