# 503M lab image. The build context is the repository root, because we build
# from our own source rather than from a published image.

# --- Stage 1: frontend assets ---
FROM node:26 AS frontend-builder
WORKDIR /app
COPY . .
RUN npm install -g corepack && corepack enable && yarn install && yarn build:static

# --- Stage 2: application ---
# bookworm, not bullseye: Debian 11 is archived, so apt-get update fails on it.
FROM python:3.13-slim-bookworm AS app
# Check-Valid-Until=false: the bookworm-updates Release can read as "expired"
# against a later build-host clock, which fails apt-get update with exit 100.
RUN apt-get -o Acquire::Check-Valid-Until=false update && apt-get install -yqq \
      postgresql-client curl \
 && rm -rf /var/lib/apt/lists/*

COPY src/       /opt/meridian/src/
COPY standalone/ /opt/meridian/standalone/
COPY --from=frontend-builder /app/src/helpdesk/static/helpdesk/vendor \
     /opt/meridian/src/helpdesk/static/helpdesk/vendor
COPY pyproject.toml README.rst /opt/meridian/
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN pip3 install --upgrade pip packaging
WORKDIR /opt/meridian
ENV UV_SYSTEM_PYTHON=1
RUN uv sync
RUN uv pip install -r /opt/meridian/standalone/requirements.txt

WORKDIR /opt/meridian/standalone
ENV DJANGO_SETTINGS_MODULE=standalone.config.settings
ENV PYTHONPATH=/opt/meridian/src:/opt/meridian
RUN MERIDIAN_SECRET_KEY=build-only python3 manage.py collectstatic --noinput
RUN chmod +x /opt/meridian/standalone/entrypoint.sh
# The lab compose file overrides this with /lab/entrypoint.sh, which also runs
# the seed. This default keeps the image usable on its own.
ENTRYPOINT [ "/opt/meridian/standalone/entrypoint.sh" ]
