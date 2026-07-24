from __future__ import annotations

import argparse
import json
import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:6006"

TRACE_LOOKUP_QUERY = """
query($traceId: String!) {
  trace: getTraceByOtelId(traceId: $traceId) {
    traceId
    project { name }
  }
}
"""

SPAN_LOOKUP_QUERY = """
query($spanId: String!) {
  span: getSpanByOtelId(spanId: $spanId) {
    spanId
    name
    trace { traceId }
    project { name }
  }
}
"""

TRACE_STATES_QUERY = """
query($traceId: String!, $first: Int!) {
  trace: getTraceByOtelId(traceId: $traceId) {
    traceId
    project { name }
    startTime
    endTime
    latencyMs
    errorCount
    spans(first: $first) {
      edges {
        node {
          spanId
          parentId
          name
          spanKind
          statusCode
          propagatedStatusCode
          statusMessage
          startTime
          endTime
          latencyMs
          metadata
          input { value }
          output { value }
        }
      }
    }
  }
}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print a minimal before/after state timeline for Phoenix LangGraph nodes."
    )
    parser.add_argument("id", help="Phoenix/OpenTelemetry trace ID or span ID.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("PHOENIX_BASE_URL", DEFAULT_BASE_URL),
        help=f"Phoenix base URL. Defaults to PHOENIX_BASE_URL or {DEFAULT_BASE_URL}.",
    )
    parser.add_argument("--first", type=int, default=100, help="Maximum spans to fetch.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    base_url = args.base_url.rstrip("/")
    try:
        report = build_report(base_url=base_url, lookup_id=args.id, first=args.first)
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        error = {"status": "error", "message": str(exc), "base_url": base_url, "lookup_id": args.id}
        print(json.dumps(error, ensure_ascii=False, indent=2) if args.json else error["message"])
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_report(report))
    return 0


def build_report(*, base_url: str, lookup_id: str, first: int) -> dict[str, Any]:
    lookup = resolve_id(base_url=base_url, lookup_id=lookup_id)
    payload = graphql(
        base_url,
        TRACE_STATES_QUERY,
        {"traceId": lookup["trace_id"], "first": max(1, first)},
    )
    trace = payload["data"]["trace"]
    if trace is None:
        raise RuntimeError(f'Phoenix trace "{lookup["trace_id"]}" was not found.')

    spans = [edge["node"] for edge in trace["spans"]["edges"]]
    node_spans = [
        span
        for span in sorted(spans, key=lambda item: str(item.get("startTime") or ""))
        if should_show_span(span)
    ]
    return {
        "status": "ok",
        "base_url": base_url,
        "lookup": lookup,
        "trace": {
            "trace_id": trace["traceId"],
            "project": trace["project"]["name"],
            "start_time": trace["startTime"],
            "end_time": trace["endTime"],
            "latency_ms": trace["latencyMs"],
            "error_count": trace["errorCount"],
            "url": f"{base_url}/redirects/traces/{trace['traceId']}",
        },
        "nodes": [node_state(span) for span in node_spans],
    }


def resolve_id(*, base_url: str, lookup_id: str) -> dict[str, Any]:
    trace = graphql(base_url, TRACE_LOOKUP_QUERY, {"traceId": lookup_id})["data"]["trace"]
    if trace is not None:
        return {
            "input_id": lookup_id,
            "kind": "trace",
            "trace_id": trace["traceId"],
            "project": trace["project"]["name"],
        }

    span = graphql(base_url, SPAN_LOOKUP_QUERY, {"spanId": lookup_id})["data"]["span"]
    if span is None:
        raise RuntimeError(f'Phoenix ID "{lookup_id}" was not found as a trace or span.')
    return {
        "input_id": lookup_id,
        "kind": "span",
        "span_id": span["spanId"],
        "span_name": span["name"],
        "trace_id": span["trace"]["traceId"],
        "project": span["project"]["name"],
    }


def graphql(base_url: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(
        f"{base_url}/graphql",
        json={"query": query, "variables": variables},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        messages = "; ".join(str(error.get("message", error)) for error in payload["errors"])
        raise RuntimeError(f"Phoenix GraphQL error: {messages}")
    return payload


def should_show_span(span: dict[str, Any]) -> bool:
    metadata = parse_json(span.get("metadata"))
    node = metadata.get("langgraph_node") if isinstance(metadata, dict) else None
    return bool(node and span.get("name") == node)


def node_state(span: dict[str, Any]) -> dict[str, Any]:
    metadata = parse_json(span.get("metadata"))
    before = state_summary(load_json_path(span, "input", "value"))
    after = state_summary(load_json_path(span, "output", "value"))
    return {
        "node": metadata.get("langgraph_node") if isinstance(metadata, dict) else None,
        "span_id": span["spanId"],
        "kind": span["spanKind"],
        "status": span["statusCode"],
        "propagated_status": span["propagatedStatusCode"],
        "status_message": span.get("statusMessage") or None,
        "latency_ms": span["latencyMs"],
        "before": before,
        "after": after,
        "changed": sorted(state_diff(before, after)),
    }


def state_summary(value: Any) -> dict[str, Any]:
    state = parse_json(value)
    if not isinstance(state, dict):
        return {}

    response = as_dict(state.get("response"))
    audit = as_dict(state.get("audit"))
    tool_context = as_dict(state.get("tool_context"))
    proposed_action = as_dict(tool_context.get("proposed_action"))
    last_tool_result = as_dict(tool_context.get("last_tool_result")) or last_list_dict(
        tool_context.get("tool_results")
    )
    messages = state.get("messages")

    summary = {
        "last_node": last_item(audit.get("node_path")),
        "messages": len(messages) if isinstance(messages, list) else None,
        "last_message": last_message_summary(messages),
        "response": compact_response(response),
        "tool": compact_tool_state(tool_context, proposed_action, last_tool_result),
        "warnings": audit.get("warnings"),
        "errors": audit.get("errors"),
    }
    return remove_empty(summary)


def compact_response(response: dict[str, Any]) -> dict[str, Any]:
    return remove_empty(
        {
            "mode": response.get("mode"),
            "user_message": response.get("user_message"),
        }
    )


def compact_tool_state(
    tool_context: dict[str, Any], proposed_action: dict[str, Any], last_tool_result: dict[str, Any]
) -> dict[str, Any]:
    return remove_empty(
        {
            "loop_count": tool_context.get("loop_count"),
            "proposed": proposed_action.get("tool_name"),
            "last_result": remove_empty(
                {
                    "tool_name": last_tool_result.get("tool_name"),
                    "status": last_tool_result.get("status"),
                    "action": load_json_path(last_tool_result, "data", "capture_action"),
                    "reason": load_json_path(last_tool_result, "data", "reason"),
                    "error": last_tool_result.get("error"),
                }
            ),
        }
    )


def state_diff(before: dict[str, Any], after: dict[str, Any]) -> set[str]:
    keys = sorted(set(before) | set(after))
    diff: set[str] = set()
    for key in keys:
        if before.get(key) != after.get(key):
            diff.add(key)
    return diff


def format_report(report: dict[str, Any]) -> str:
    trace = report["trace"]
    lines = [
        f"Phoenix node states: {report['lookup']['input_id']} ({report['lookup']['kind']})",
        f"Trace: {trace['trace_id']}",
        f"Project: {trace['project']}",
        f"URL: {trace['url']}",
        f"Latency: {trace['latency_ms']} ms | errors: {trace['error_count']}",
        "",
    ]
    for index, node in enumerate(report["nodes"], start=1):
        lines.append(f"{index}. {node['node']} status={node['status']} latency={node['latency_ms']}ms")
        if node.get("status_message"):
            lines.append(f"   status_message: {node['status_message']}")
        lines.append(f"   before: {state_line(node['before'])}")
        lines.append(f"   after:  {state_line(node['after'])}")
        if node["changed"]:
            lines.append(f"   changed: {', '.join(node['changed'])}")
        lines.append("")
    return "\n".join(lines).rstrip()


def state_line(state: dict[str, Any]) -> str:
    if not state:
        return "{}"
    parts = []
    if state.get("last_node"):
        parts.append(f"node={state['last_node']}")
    if state.get("messages") is not None:
        parts.append(f"messages={state['messages']}")
    if state.get("last_message"):
        parts.append(f"last={inline_json(state['last_message'])}")
    if state.get("tool"):
        parts.append(f"tool={inline_json(state['tool'])}")
    if state.get("response"):
        parts.append(f"response={inline_json(state['response'])}")
    if state.get("warnings"):
        parts.append(f"warnings={inline_json(state['warnings'])}")
    if state.get("errors"):
        parts.append(f"errors={inline_json(state['errors'])}")
    return " ".join(parts)


def inline_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_json(value: Any) -> Any:
    if not isinstance(value, str) or not value:
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def load_json_path(value: Any, *path: str) -> Any:
    current = parse_json(value)
    for key in path:
        if not isinstance(current, dict):
            return None
        current = parse_json(current.get(key))
    return current


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def last_list_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[-1], dict):
        return value[-1]
    return {}


def last_item(value: Any) -> Any:
    return value[-1] if isinstance(value, list) and value else None


def last_message_summary(messages: Any) -> dict[str, Any]:
    if not isinstance(messages, list) or not messages:
        return {}
    message = messages[-1]
    if not isinstance(message, dict):
        return {}
    data = as_dict(message.get("data"))
    tool_payload = parse_json(data.get("content"))
    if isinstance(tool_payload, dict) and tool_payload.get("tool_name"):
        return remove_empty(
            {
                "type": "tool",
                "tool_name": tool_payload.get("tool_name"),
                "status": tool_payload.get("status"),
                "action": load_json_path(tool_payload, "data", "capture_action"),
                "reason": load_json_path(tool_payload, "data", "reason"),
            }
        )
    tool_calls = data.get("tool_calls")
    return remove_empty(
        {
            "type": message.get("type") or data.get("type"),
            "tool_calls": [
                {"name": call.get("name")}
                for call in tool_calls
                if isinstance(call, dict)
            ]
            if isinstance(tool_calls, list)
            else None,
            "tool_status": data.get("status"),
        }
    )


def remove_empty(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {key: remove_empty(item) for key, item in value.items()}
        return {
            key: item
            for key, item in cleaned.items()
            if item not in (None, "", [], {})
        }
    if isinstance(value, list):
        return [remove_empty(item) for item in value if item not in (None, "", [], {})]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
