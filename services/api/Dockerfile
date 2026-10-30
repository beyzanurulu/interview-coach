FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.11.32
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

COPY app ./app
ENV PATH="/app/.venv/bin:$PATH" PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
