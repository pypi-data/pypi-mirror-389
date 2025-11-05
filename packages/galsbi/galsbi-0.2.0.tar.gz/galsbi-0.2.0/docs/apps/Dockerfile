FROM ghcr.io/astral-sh/uv:bookworm-slim

RUN  uv python install 3.12 && uv venv --python 3.12 && uv pip install numpy plotly dash cosmic-toolbox
RUN  mkdir -p /app/pages

ENTRYPOINT ["/.venv/bin/python", "/app/app.py"]
