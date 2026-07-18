import json

from tools.contracts import ToolResult


def to_mcp_content(result: ToolResult):
    import mcp.types as types

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result.model_dump(mode="json"), ensure_ascii=False),
        )
    ]
