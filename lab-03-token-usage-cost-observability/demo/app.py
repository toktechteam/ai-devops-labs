import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import boto3
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)


DEFAULT_API_URL = os.environ.get("API_INVOKE_URL", "")
DEFAULT_AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")
DEFAULT_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
DEFAULT_NAMESPACE = os.environ.get("METRICS_NAMESPACE", "Lab02/BedrockGateway")
DEFAULT_MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
DEFAULT_SERVICE_DIM = os.environ.get("SERVICE_DIMENSION", "llm-gateway")


def _invoke_api(api_url: str, token: str, prompt: str) -> tuple[int, dict]:
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
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


def _metric_queries(namespace: str, model_id: str, service: str, period: int) -> list[dict]:
    metric_names = [
        "InputTokens",
        "OutputTokens",
        "TotalTokens",
        "EstimatedCostUSD",
        "RequestCount",
        "LatencyMs",
        "ModelLatencyMs",
        "NonModelLatencyMs",
        "ApiGatewayToLambdaMs",
    ]
    stat_map = {
        "InputTokens": "Sum",
        "OutputTokens": "Sum",
        "TotalTokens": "Sum",
        "EstimatedCostUSD": "Sum",
        "RequestCount": "Sum",
        "LatencyMs": "Average",
        "ModelLatencyMs": "Average",
        "NonModelLatencyMs": "Average",
        "ApiGatewayToLambdaMs": "Average",
    }
    queries = []
    for idx, name in enumerate(metric_names):
        queries.append(
            {
                "Id": f"m{idx}",
                "Label": name,
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,
                        "MetricName": name,
                        "Dimensions": [
                            {"Name": "Service", "Value": service},
                            {"Name": "ModelId", "Value": model_id},
                        ],
                    },
                    "Period": period,
                    "Stat": stat_map.get(name, "Average"),
                },
                "ReturnData": True,
            }
        )
    return queries


def _format_series(timestamps: list, values: list) -> list[dict]:
    series = []
    for ts, val in zip(timestamps, values):
        if not ts:
            continue
        series.append({"ts": ts.isoformat(), "value": val})
    return series


@app.route("/")
def index():
    return render_template(
        "index.html",
        default_api_url=DEFAULT_API_URL,
        default_auth_token=DEFAULT_AUTH_TOKEN,
        default_namespace=DEFAULT_NAMESPACE,
        default_region=DEFAULT_REGION,
        default_model_id=DEFAULT_MODEL_ID,
    )


@app.route("/api/invoke", methods=["POST"])
def invoke():
    data = request.get_json(silent=True) or {}
    api_url = data.get("api_url") or DEFAULT_API_URL
    token = data.get("auth_token") or DEFAULT_AUTH_TOKEN
    prompt = (data.get("prompt") or "").strip()

    if not api_url:
        return jsonify({"error": "API URL is required"}), 400
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    status, payload = _invoke_api(api_url, token, prompt)
    return jsonify({"status": status, "payload": payload})


@app.route("/api/metrics", methods=["GET"])
def metrics():
    namespace = request.args.get("namespace", DEFAULT_NAMESPACE)
    region = request.args.get("region", DEFAULT_REGION)
    model_id = request.args.get("model_id", DEFAULT_MODEL_ID)
    service = request.args.get("service", DEFAULT_SERVICE_DIM)

    minutes = int(request.args.get("minutes", "30"))
    period = int(request.args.get("period", "60"))

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)

    client = boto3.client("cloudwatch", region_name=region)
    queries = _metric_queries(namespace, model_id, service, period)

    response = client.get_metric_data(
        MetricDataQueries=queries,
        StartTime=start,
        EndTime=end,
        ScanBy="TimestampAscending",
        MaxDatapoints=500,
    )

    results = {}
    for result in response.get("MetricDataResults", []):
        metric_name = result.get("Label") or result.get("Id")
        timestamps = result.get("Timestamps", [])
        values = result.get("Values", [])
        series = _format_series(timestamps, values)
        results[metric_name] = series

    return jsonify(
        {
            "namespace": namespace,
            "region": region,
            "model_id": model_id,
            "service": service,
            "period": period,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "metrics": results,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)
