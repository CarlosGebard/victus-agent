FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VICTUS_MCP_HTTP_HOST=0.0.0.0 \
    VICTUS_MCP_HTTP_PORT=8765

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project --extra phoenix --extra safety-index

COPY src ./src
COPY ops ./ops
COPY config ./config

EXPOSE 8765 8766

CMD ["uv", "run", "--no-sync", "python", "-m", "adapters.mcp.transport"]
