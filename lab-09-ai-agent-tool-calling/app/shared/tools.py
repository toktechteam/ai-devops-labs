from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class ToolCallResult:
    name: str
    tool_input: dict
    output: dict
    duration_ms: float


def _tool_duration(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def list_ec2_instances(params: dict) -> dict:
    region = params.get("region", "us-east-1")
    owner = params.get("owner", "theopskart")
    instances = [
        {
            "instance_id": "i-0a12bc34d5e6f7890",
            "name": "ops-api-prod-1",
            "state": "running",
            "type": "t3.large",
            "az": f"{region}a",
        },
        {
            "instance_id": "i-1b23cd45e6f7a8901",
            "name": "ops-worker-prod-2",
            "state": "running",
            "type": "t3.medium",
            "az": f"{region}b",
        },
        {
            "instance_id": "i-2c34de56f7a8b9012",
            "name": "ops-batch-prod-1",
            "state": "stopped",
            "type": "t3.small",
            "az": f"{region}c",
        },
    ]
    return {
        "region": region,
        "owner": owner,
        "instances": instances,
    }


def get_ec2_health(params: dict) -> dict:
    instance_ids = params.get("instance_ids", [])
    checks = []
    for idx, instance_id in enumerate(instance_ids):
        status = "ok" if idx % 2 == 0 else "impaired"
        checks.append(
            {
                "instance_id": instance_id,
                "status": status,
                "cpu_utilization": 24 + idx * 8,
                "disk_io": 110 + idx * 40,
            }
        )
    return {
        "checks": checks,
        "summary": {
            "total": len(checks),
            "impaired": sum(1 for item in checks if item["status"] != "ok"),
        },
    }


def search_runbooks(params: dict) -> dict:
    query = params.get("query", "")
    return {
        "query": query,
        "matches": [
            {
                "id": "RB-201",
                "title": "EC2 CPU spike mitigation",
                "score": 0.91,
            },
            {
                "id": "RB-118",
                "title": "Investigate unhealthy instances",
                "score": 0.83,
            },
        ],
    }


def create_ticket(params: dict) -> dict:
    return {
        "ticket_id": "OPS-1042",
        "status": "open",
        "priority": params.get("priority", "P2"),
        "summary": params.get("summary", "Investigate instance health"),
    }


ToolHandler = Callable[[dict], dict]

TOOLS: dict[str, ToolHandler] = {
    "aws.ec2.list_instances": list_ec2_instances,
    "aws.ec2.get_health": get_ec2_health,
    "ops.runbook.search": search_runbooks,
    "ops.ticket.create": create_ticket,
}


def run_tool(name: str, tool_input: dict) -> ToolCallResult:
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    start = time.perf_counter()
    output = TOOLS[name](tool_input)
    return ToolCallResult(
        name=name,
        tool_input=tool_input,
        output=output,
        duration_ms=_tool_duration(start),
    )
