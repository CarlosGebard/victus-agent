from __future__ import annotations

import argparse
import json
import os
import textwrap
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:6006"

TRACE_LOOKUP_QUERY = """
query($traceId: String!) {
  trace: getTraceByOtelId(traceId: $traceId) {
    id
    traceId
    project { id name }
  }
}
"""

SPAN_LOOKUP_QUERY = """
query($spanId: String!) {
  span: getSpanByOtelId(spanId: $spanId) {
    id
    spanId
    name
    trace { id traceId }
    project { id name }
  }
}
"""

TRACE_DETAIL_QUERY = """
query($traceId: String!, $first: Int!) {
  trace: getTraceByOtelId(traceId: $traceId) {
    id
    traceId
    startTime
    endTime
    latencyMs
    numSpans
    errorCount
    project { id name }
    rootSpan {
      id
      spanId
      parentId
      name
      statusCode
      statusMessage
      propagatedStatusCode
      spanKind
      startTime
      endTime
      latencyMs
      attributes
      metadata
      tokenCountTotal
      tokenCountPrompt
      tokenCountCompletion
      output { value }
      events { name message timestamp }
    }
    spans(first: $first) {
      edges {
        node {
          id
          spanId
          parentId
          name
          statusCode
          statusMessage
          propagatedStatusCode
          spanKind
          startTime
          endTime
          latencyMs
          attributes
          metadata
          tokenCountTotal
          tokenCountPrompt
          tokenCountCompletion
          output { value }
          events { name message timestamp }
        }
      }
    }
  }
}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Look up a Phoenix trace by trace ID or span ID and print a compact diagnosis."
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
        report = lookup_trace(base_url=base_url, lookup_id=args.id, first=args.first)
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        error = {"status": "error", "message": str(exc), "base_url": base_url, "lookup_id": args.id}
        print(json.dumps(error, ensure_ascii=False, indent=2) if args.json else error["message"])
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    return 0


def lookup_trace(*, base_url: str, lookup_id: str, first: int) -> dict[str, Any]:
    resolved = resolve_id(base_url=base_url, lookup_id=lookup_id)
    trace_id = resolved["trace_id"]
    payload = graphql(
        base_url,
        TRACE_DETAIL_QUERY,
        {"traceId": trace_id, "first": max(1, first)},
    )
    trace = payload["data"]["trace"]
    if trace is None:
        raise RuntimeError(f'Phoenix trace "{trace_id}" was not found.')

    spans = [edge["node"] for edge in trace["spans"]["edges"]]
    root_span = trace.get("rootSpan")
    if root_span and all(span["id"] != root_span["id"] for span in spans):
        spans.insert(0, root_span)

    findings = extract_findings(root_span or {})
    error_spans = [
        compact_span(span)
        for span in spans
        if span.get("statusCode") == "ERROR" or span.get("propagatedStatusCode") == "ERROR"
    ]

    return {
        "status": "ok",
        "base_url": base_url,
        "lookup": resolved,
        "trace": {
            "id": trace["id"],
            "trace_id": trace["traceId"],
            "project": trace["project"],
            "start_time": trace["startTime"],
            "end_time": trace["endTime"],
            "latency_ms": trace["latencyMs"],
            "num_spans": trace["numSpans"],
            "fetched_spans": len(spans),
            "error_count": trace["errorCount"],
            "url": f"{base_url}/redirects/traces/{trace['traceId']}",
        },
        "findings": findings,
        "error_spans": error_spans,
        "spans": [compact_span(span) for span in sorted_spans(spans)],
    }


def resolve_id(*, base_url: str, lookup_id: str) -> dict[str, Any]:
    trace_payload = graphql(base_url, TRACE_LOOKUP_QUERY, {"traceId": lookup_id})
    trace = trace_payload["data"]["trace"]
    if trace is not None:
        return {
            "input_id": lookup_id,
            "kind": "trace",
            "trace_id": trace["traceId"],
            "project": trace["project"],
            "url": f"{base_url}/redirects/traces/{trace['traceId']}",
        }

    span_payload = graphql(base_url, SPAN_LOOKUP_QUERY, {"spanId": lookup_id})
    span = span_payload["data"]["span"]
    if span is None:
        raise RuntimeError(f'Phoenix ID "{lookup_id}" was not found as a trace or span.')
    return {
        "input_id": lookup_id,
        "kind": "span",
        "span_id": span["spanId"],
        "span_name": span["name"],
        "trace_id": span["trace"]["traceId"],
        "project": span["project"],
        "url": f"{base_url}/redirects/spans/{span['spanId']}",
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


def extract_findings(root_span: dict[str, Any]) -> dict[str, Any]:
    output = load_json_path(root_span, "output", "value")
    state = parse_json(output)
    if not isinstance(state, dict):
        return {}

    request = state.get("request") if isinstance(state.get("request"), dict) else {}
    response = state.get("response") if isinstance(state.get("response"), dict) else {}
    audit = state.get("audit") if isinstance(state.get("audit"), dict) else {}
    tool_context = state.get("tool_context") if isinstance(state.get("tool_context"), dict) else {}
    last_tool_result = tool_context.get("last_tool_result")
    if not isinstance(last_tool_result, dict):
        tool_results = tool_context.get("tool_results")
        if isinstance(tool_results, list) and tool_results:
            last_tool_result = tool_results[-1]

    finding: dict[str, Any] = {
        "request_id": request.get("request_id"),
        "user_id": request.get("user_id"),
        "conversation_id": request.get("conversation_id"),
        "original_text": request.get("original_text") or request.get("raw_text"),
        "response_mode": response.get("mode"),
        "user_message": response.get("user_message"),
        "audit_errors": audit.get("errors") or [],
        "audit_warnings": audit.get("warnings") or [],
        "node_path": audit.get("node_path") or [],
    }
    if isinstance(last_tool_result, dict):
        finding["last_tool_result"] = {
            "tool_name": last_tool_result.get("tool_name"),
            "status": last_tool_result.get("status"),
            "reason": load_json_path(last_tool_result, "data", "reason"),
            "error": last_tool_result.get("error"),
        }
    return {key: value for key, value in finding.items() if value not in (None, "", [])}


def compact_span(span: dict[str, Any]) -> dict[str, Any]:
    metadata = parse_json(span.get("metadata"))
    attributes = parse_json(span.get("attributes"))
    events = span.get("events") or []
    return {
        "id": span.get("id"),
        "span_id": span.get("spanId"),
        "parent_id": span.get("parentId"),
        "name": span.get("name"),
        "kind": span.get("spanKind"),
        "status": span.get("statusCode"),
        "propagated_status": span.get("propagatedStatusCode"),
        "status_message": span.get("statusMessage") or None,
        "latency_ms": span.get("latencyMs"),
        "tokens": {
            "total": span.get("tokenCountTotal"),
            "prompt": span.get("tokenCountPrompt"),
            "completion": span.get("tokenCountCompletion"),
        },
        "langgraph_node": load_json_path(metadata, "langgraph_node"),
        "llm_model": load_json_path(attributes, "llm", "model_name"),
        "llm_operation": load_json_path(attributes, "victus", "llm", "operation"),
        "events": [
            {
                "name": event.get("name"),
                "message": event.get("message"),
                "timestamp": event.get("timestamp"),
            }
            for event in events
        ],
    }


def sorted_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(spans, key=lambda span: str(span.get("startTime") or ""))


def format_report(report: dict[str, Any]) -> str:
    trace = report["trace"]
    lookup = report["lookup"]
    lines = [
        f"Phoenix lookup: {lookup['input_id']} ({lookup['kind']})",
        f"Project: {trace['project']['name']}",
        f"Trace: {trace['trace_id']}",
        f"URL: {trace['url']}",
        f"Latency: {trace['latency_ms']} ms | spans: {trace['fetched_spans']}/{trace['num_spans']} | errors: {trace['error_count']}",
    ]
    if lookup["kind"] == "span":
        lines.append(f"Resolved from span: {lookup['span_id']} ({lookup['span_name']})")

    findings = report.get("findings") or {}
    if findings:
        lines.extend(["", "Agent findings:"])
        for key in ("request_id", "conversation_id", "original_text", "response_mode", "user_message"):
            if findings.get(key):
                lines.append(f"  {key}: {findings[key]}")
        if tool := findings.get("last_tool_result"):
            lines.append(
                "  last_tool_result: "
                f"{tool.get('tool_name')} -> {tool.get('status')}"
                + (f" ({tool.get('reason')})" if tool.get("reason") else "")
            )
        if findings.get("audit_errors"):
            lines.append(f"  audit_errors: {findings['audit_errors']}")
        if findings.get("audit_warnings"):
            lines.append(f"  audit_warnings: {findings['audit_warnings']}")
        if findings.get("node_path"):
            lines.append(f"  node_path: {' -> '.join(findings['node_path'])}")

    if report["error_spans"]:
        lines.extend(["", "Error spans:"])
        for span in report["error_spans"]:
            lines.append(format_span_line(span))

    lines.extend(["", "Spans:"])
    for span in report["spans"]:
        lines.append(format_span_line(span))
        for event in span["events"]:
            message = event.get("message") or ""
            lines.append(f"    event: {event.get('name')} {shorten(message, 140)}".rstrip())
    return "\n".join(lines)


def format_span_line(span: dict[str, Any]) -> str:
    parts = [
        f"  - {span['name']}",
        f"[{span['kind']}]",
        f"status={span['status']}/{span['propagated_status']}",
        f"latency={span['latency_ms']}ms",
        f"span={span['span_id']}",
    ]
    if span.get("langgraph_node"):
        parts.append(f"node={span['langgraph_node']}")
    if span.get("llm_model"):
        parts.append(f"model={span['llm_model']}")
    if span.get("status_message"):
        parts.append(f"message={shorten(span['status_message'], 120)}")
    tokens = span.get("tokens") or {}
    if tokens.get("total"):
        parts.append(
            f"tokens={tokens['total']} "
            f"(prompt={tokens.get('prompt')}, completion={tokens.get('completion')})"
        )
    return " ".join(parts)


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


def shorten(value: Any, width: int) -> str:
    return textwrap.shorten(str(value), width=width, placeholder="...")


if __name__ == "__main__":
    raise SystemExit(main())
