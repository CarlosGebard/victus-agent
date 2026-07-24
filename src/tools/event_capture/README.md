# event_capture

Captures meals and beverages as `meal.logged` domain events. Each item requires a numeric quantity
in grams (`g`) or milliliters (`ml`); missing quantities return a clarification request. The
occurrence time defaults to today.

- Input/result: `contract.py`
- Rules: `policy.py`
- Event construction: `actions.py`
- Public execution: `tool.py`

Missing meal details return `needs_clarification`. Other event categories are not accepted by this
tool.
All callers invoke the catalog definition through `ToolRuntime`.
