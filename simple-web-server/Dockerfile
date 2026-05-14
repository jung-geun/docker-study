FROM ghcr.io/astral-sh/uv:trixie

WORKDIR /app

COPY app.py .

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

ENV APP_NAME="My First Container"

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "app.py"]