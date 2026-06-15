FROM astral/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
RUN uv sync --frozen --no-dev

# Copy application source code
COPY src ./src

# Ensure the virtualenv path is in the environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default port (FastAPI)
EXPOSE 8000

# Default run command (overridden for bridge service in docker-compose)
CMD ["uvicorn", "src.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
