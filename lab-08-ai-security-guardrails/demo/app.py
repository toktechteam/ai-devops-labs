import json
import os
import urllib.error
import urllib.request

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

DEFAULT_INVOKE_URL = os.environ.get("INVOKE_API_URL", "")
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


@app.route("/")
def index():
    return render_template(
        "index.html",
        default_invoke_url=DEFAULT_INVOKE_URL,
        default_auth_token=DEFAULT_AUTH_TOKEN,
    )


@app.route("/api/invoke", methods=["POST"])
def invoke():
    data = request.get_json(silent=True) or {}
    api_url = data.get("invoke_url") or DEFAULT_INVOKE_URL
    token = data.get("auth_token") or DEFAULT_AUTH_TOKEN

    if not api_url:
        return jsonify({"error": "Invoke URL is required"}), 400

    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    payload = {
        "prompt": prompt,
        "model_id": (data.get("model_id") or "").strip() or None,
        "temperature": float(data.get("temperature") or 0.2),
        "policy_mode": (data.get("policy_mode") or "").strip() or None,
        "allow_override": bool(data.get("allow_override")),
        "enable_output_filter": bool(data.get("enable_output_filter")),
    }

    status, response = _post_json(api_url, token, payload)
    return jsonify({"status": status, "payload": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)
