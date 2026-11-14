FROM python:3.12-slim

WORKDIR /app

# Copy the agent service
COPY services/agent_services/pyproject.toml .
COPY services/agent_services/app ./app

# Copy the WebGuide package
COPY services/webguide_service/pyproject.toml ./webguide_service/pyproject.toml
COPY services/webguide_service/__init__.py ./webguide_service/__init__.py
COPY services/webguide_service/app ./webguide_service/app

# Install both Python packages
RUN pip install --no-cache-dir ./webguide_service \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]