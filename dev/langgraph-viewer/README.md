# Victus LangGraph Viewer

Development-only LangGraph visualization harness.

This directory should not become a second Victus runtime. It exists only to inspect and debug graph shape while the production runtime is implemented in the main repository.

Ignored local artifacts:

- `.venv/`
- `.env`
- `.langgraph_api/`
- nested `.git/`

Target integration:

1. import the real Victus graph from the main package
2. expose it through `langgraph.json`
3. run it locally for visualization only
