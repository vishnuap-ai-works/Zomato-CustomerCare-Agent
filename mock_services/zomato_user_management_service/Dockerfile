FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml .
COPY uv.lock .
RUN uv pip install --system fastapi uvicorn pydantic sqlalchemy
COPY mock_services /app/mock_services
CMD ["uvicorn", "mock_services.zomato_user_management_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
