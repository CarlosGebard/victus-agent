# Implemented Tools

## Tool Model

Every tool has a typed input contract and one implementation. The canonical catalog registers its
name, purpose, risk, side effects, and supported interfaces. `ToolRuntime` validates and executes the
same implementation for every adapter.

Canonical registry: `src/tools/catalog.py`

## Tools

- `event_capture` — Captures concrete user events such as meals, symptoms, biometrics, sleep, or
  exercise. Path: `src/tools/event_capture/tool.py`
- `profile_update` — Updates durable profile information such as restrictions and preferences.
  Path: `src/tools/profile/tool.py`
- `planning` — Manages goals, planning sessions, revisions, and validated planning artifacts.
  Path: `src/tools/planning/tool.py`
- `feedback` — Records or resolves user feedback about a plan, recommendation, meal, or answer.
  Path: `src/tools/feedback/tool.py`
- `evidence_answer` — Persists grounded claims and their supporting citations.
  Path: `src/tools/evidence/tool.py`
- `clarification` — Requests missing information and resumes the pending workflow when resolved.
  Path: `src/tools/interaction/clarification.py`
- `confirmation` — Requests explicit approval and resumes the pending action when resolved.
  Path: `src/tools/interaction/confirmation.py`
- `recuperar_perfil` — Retrieves the authenticated user's current Victus profile without modifying
  it. Path: `src/tools/profile/remote.py`

## Tool Result Contract

Every tool returns the same envelope. Tool-specific output belongs in `data`; execution status,
persisted event references, safety, tracing, and errors remain stable across every adapter.

Source: `src/tools/contracts.py`

```ts
type ToolStatus =
  | "success"
  | "needs_clarification"
  | "blocked"
  | "rejected"
  | "error"

type ToolEventRef = {
  event_id: string
  event_type: string
  seq: number
}

type ClarificationRequest = {
  missing_fields: string[]
  question: string
  expected_answer_type:
    | "quantity"
    | "time"
    | "meal_reference"
    | "preference_strength"
    | "restriction_type"
    | "goal_target"
    | "yes_no"
    | "free_text"
  resume_node?: string
  resume_action?: string
}

type ToolResult = {
  status: ToolStatus
  data?: unknown
  events_emitted: ToolEventRef[]
  warnings: string[]
  clarification?: ClarificationRequest
  safety: {
    status: "ok" | "warning" | "blocked" | "needs_clarification"
    reasons: string[]
  }
  meta: {
    confidence?: number
    schema_version: 1
    handler_version?: string
    trace_id?: string
  }
  error?: {
    code: string
    message: string
  }
}
```

Rules:

- `success` means the requested action completed.
- `needs_clarification` means execution must pause for missing information.
- `blocked` means safety or policy prevented execution.
- `rejected` means the invocation was invalid.
- `error` means execution failed unexpectedly.
- `events_emitted` contains references only after durable persistence.
- Unvalidated model output must never become persisted tool state.
