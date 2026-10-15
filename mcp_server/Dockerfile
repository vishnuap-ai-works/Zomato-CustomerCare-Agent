FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml .
COPY uv.lock* ./
RUN uv pip install --system "mcp<2" uvicorn requests starlette httpx
COPY mcp_server /app/mcp_server
CMD ["uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8003"]
