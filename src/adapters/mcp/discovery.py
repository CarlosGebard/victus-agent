from tools.catalog import list_tools


def discover_tools():
    import mcp.types as types

    return [
        types.Tool(
            name=definition.name,
            description=definition.description,
            inputSchema=definition.input_schema,
        )
        for definition in list_tools(exposure="mcp")
    ]
