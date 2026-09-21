FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml .
COPY uv.lock .
RUN uv pip install --system fastapi uvicorn pydantic requests sqlalchemy langchain langchain-openai langchain-ollama langchain-community google-search-results
COPY agent /app/agent
# We also need mock_services for the shared DB models? No, the agent doesn't use the DB directly!
CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
