# event_capture

Captures meals, biometrics, lifestyle metrics, and symptoms as domain events.

- Input/result: `contract.py`
- Rules: `policy.py`
- Event construction: `actions.py`
- Public execution: `tool.py`

Safety-sensitive symptoms return `blocked`; ambiguous input returns `needs_clarification`.
All callers invoke the catalog definition through `ToolRuntime`.
