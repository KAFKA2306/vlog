FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /usr/local/bin/
COPY --from=oven/bun:1.3.14 /usr/local/bin/bun /usr/local/bin/bun

RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin v3.52.0

ENV UV_PYTHON=3.12
