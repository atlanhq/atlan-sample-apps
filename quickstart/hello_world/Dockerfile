FROM registry.atlan.com/public/app-runtime-base:3

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen

COPY app/ app/

ENV ATLAN_APP_MODULE=app.connector:HelloWorldApp
