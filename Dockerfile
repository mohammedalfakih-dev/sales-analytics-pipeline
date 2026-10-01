FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/
COPY data/sample/ data/sample/
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "src.pipeline"]
