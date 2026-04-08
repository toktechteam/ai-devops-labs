import os
from typing import Any

from shared.bedrock_llm import generate_answer
from shared.http_utils import estimate_tokens, json_response, parse_body
from shared.logger import log
from shared.timing import StageTimer
from shared.tools import run_tool


DEFAULT_MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-pro-v1:0")
DEFAULT_TEMPERATURE = float(os.environ.get("DEFAULT_TEMPERATURE", "0.2"))
DEFAULT_TOOL_STRATEGY = os.environ.get("DEFAULT_TOOL_STRATEGY", "auto")
MAX_TOOL_CALLS = int(os.environ.get("MAX_TOOL_CALLS", "4"))
ENABLE_MODEL = os.environ.get("ENABLE_MODEL", "true").lower() not in {"false", "0", "no"}
DEFAULT_REGION = os.environ.get("DEFAULT_REGION", "us-east-1")


def _normalize_strategy(value: str | None) -> str:
    strategy = (value or DEFAULT_TOOL_STRATEGY).strip().lower()
    if strategy in {
        "auto",
        "none",
        "force_ec2_chain",
        "force_incident_chain",
    }:
        return strategy
    return "auto"


def _decide_plan(prompt: str, strategy: str) -> tuple[str, list[str], str]:
    if strategy == "none":
        return "direct_answer", [], "Tooling disabled by strategy"
    if strategy == "force_ec2_chain":
        return "ec2_inventory", ["aws.ec2.list_instances", "aws.ec2.get_health"], "Forced EC2 chain"
    if strategy == "force_incident_chain":
        return (
            "incident_response",
            ["aws.ec2.list_instances", "aws.ec2.get_health", "ops.ticket.create"],
            "Forced incident chain",
        )

    lowered = prompt.lower()
    if "ec2" in lowered or "instance" in lowered:
        if any(keyword in lowered for keyword in ["incident", "alert", "ticket"]):
            return (
                "incident_response",
                ["aws.ec2.list_instances", "aws.ec2.get_health", "ops.ticket.create"],
                "EC2 request with incident context",
            )
        return (
            "ec2_inventory",
            ["aws.ec2.list_instances", "aws.ec2.get_health"],
            "EC2 inventory request",
        )
    if "runbook" in lowered or "playbook" in lowered:
        return "runbook_lookup", ["ops.runbook.search"], "Runbook lookup"
    if "ticket" in lowered or "incident" in lowered:
        return "incident_response", ["ops.ticket.create"], "Incident escalation"
    return "direct_answer", [], "No tools required"


def _build_tool_input(tool_name: str, prompt: str, context: dict) -> dict:
    if tool_name == "aws.ec2.list_instances":
        return {"region": context.get("region", DEFAULT_REGION), "owner": "theopskart"}
    if tool_name == "aws.ec2.get_health":
        instance_ids = [item.get("instance_id") for item in context.get("instances", [])]
        return {"instance_ids": [item for item in instance_ids if item]}
    if tool_name == "ops.runbook.search":
        return {"query": prompt}
    if tool_name == "ops.ticket.create":
        return {"summary": _build_ticket_summary(prompt, context), "priority": "P2"}
    return {}


def _build_ticket_summary(prompt: str, context: dict) -> str:
    summary = context.get("health", {}).get("summary", {})
    impaired = summary.get("impaired", 0)
    total = summary.get("total", 0)
    return f"Agent detected {impaired} impaired of {total} instances. Prompt: {prompt[:80]}"


def _summarize_context(intent: str, context: dict) -> str:
    if intent in {"ec2_inventory", "incident_response"}:
        instances = context.get("instances", [])
        health = context.get("health", {}).get("summary", {})
        impaired = health.get("impaired", 0)
        total = health.get("total", len(instances))
        ticket = context.get("ticket")
        ticket_msg = ""
        if ticket:
            ticket_msg = f" Ticket {ticket.get('ticket_id')} opened with priority {ticket.get('priority')}."
        return (
            f"Found {len(instances)} EC2 instances. Health checks show {impaired} impaired out of {total}."
            f"{ticket_msg}"
        )
    if intent == "runbook_lookup":
        matches = context.get("runbooks", {}).get("matches", [])
        if matches:
            top = matches[0]
            return f"Top runbook match: {top.get('title')} ({top.get('id')})."
        return "No runbooks matched the query."
    return "No tools were required for this request."


def _build_model_prompt(prompt: str, intent: str, structured: dict, tool_trace: list[dict]) -> str:
    return (
        "You are an AI agent summarizing tool results for the user. "
        "Respond concisely with the key findings and next actions.\n\n"
        f"User prompt: {prompt}\n\n"
        f"Intent: {intent}\n\n"
        f"Tool outputs (JSON): {structured}\n\n"
        f"Tool call sequence: {[item.get('name') for item in tool_trace]}\n"
    )


def handler(event: dict, context: Any):
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )

    timer = StageTimer()

    with timer.stage("parse"):
        body = parse_body(event)

    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return json_response(400, {"error": "prompt is required", "request_id": request_id})

    model_id = (body.get("model_id") or "").strip() or DEFAULT_MODEL_ID
    temperature = float(body.get("temperature") or DEFAULT_TEMPERATURE)
    tool_strategy = _normalize_strategy(body.get("tool_strategy"))
    max_tool_calls = int(body.get("max_tool_calls") or MAX_TOOL_CALLS)
    use_model = body.get("use_model")
    if use_model is None:
        use_model = ENABLE_MODEL
    use_model = bool(use_model)

    context_state: dict[str, Any] = {"region": body.get("region") or DEFAULT_REGION}

    with timer.stage("plan"):
        intent, plan, plan_reason = _decide_plan(prompt, tool_strategy)
        plan = plan[: max(0, max_tool_calls)]

    tool_trace: list[dict] = []
    for tool_name in plan:
        tool_input = _build_tool_input(tool_name, prompt, context_state)
        try:
            with timer.stage(f"tool.{tool_name}"):
                result = run_tool(tool_name, tool_input)
        except Exception as exc:  # noqa: BLE001
            return json_response(
                500,
                {
                    "error": f"tool_error: {exc}",
                    "request_id": request_id,
                    "tool": tool_name,
                },
            )
        tool_trace.append(
            {
                "name": result.name,
                "input": result.tool_input,
                "output": result.output,
                "duration_ms": result.duration_ms,
            }
        )
        if tool_name == "aws.ec2.list_instances":
            context_state["instances"] = result.output.get("instances", [])
        elif tool_name == "aws.ec2.get_health":
            context_state["health"] = result.output
        elif tool_name == "ops.runbook.search":
            context_state["runbooks"] = result.output
        elif tool_name == "ops.ticket.create":
            context_state["ticket"] = result.output

    structured_output: dict[str, Any] = {}
    for key in ["instances", "health", "runbooks", "ticket"]:
        if key in context_state:
            structured_output[key] = context_state[key]

    summary = _summarize_context(intent, context_state)

    model_error = None
    answer = summary
    if use_model:
        with timer.stage("model.compose"):
            try:
                agent_prompt = _build_model_prompt(prompt, intent, structured_output, tool_trace)
                answer = generate_answer(agent_prompt, model_id, temperature) or summary
            except Exception as exc:  # noqa: BLE001
                model_error = str(exc)
                answer = summary

    with timer.stage("response.format"):
        pass

    total_ms = timer.total_ms()

    response_payload = {
        "request_id": request_id,
        "agent": {
            "intent": intent,
            "plan": plan,
            "plan_reason": plan_reason,
            "tool_strategy": tool_strategy,
            "tool_calls": tool_trace,
            "structured_output": structured_output,
            "final_answer": answer,
            "model_used": use_model,
            "model_id": model_id if use_model else None,
        },
        "latency_ms": total_ms,
        "lifecycle": timer.stages,
        "metrics": {
            "prompt_chars": len(prompt),
            "estimated_tokens": estimate_tokens(prompt),
            "tool_calls": len(tool_trace),
        },
    }

    if model_error:
        response_payload["agent"]["model_error"] = model_error

    log(
        request_id=request_id,
        intent=intent,
        tool_strategy=tool_strategy,
        tool_calls=len(tool_trace),
        model_used=use_model,
        latency_ms=total_ms,
        plan=plan,
        plan_reason=plan_reason,
        model_error=model_error,
    )

    return json_response(200, response_payload)
