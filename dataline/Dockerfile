# -------------------------------
# FRONTEND BUILD STAGE
# -------------------------------
FROM node:23-alpine AS temp-frontend
RUN apk --update --no-cache add \
    libc6-compat \
    automake \
    libtool \
    autoconf \
    build-base \
    zlib \
    zlib-dev \
    python3 make gcc g++

WORKDIR /home/dataline/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ .

ARG API_URL="/"
ENV VITE_API_URL=$API_URL
ENV NODE_ENV=local
RUN npm run build

# -------------------------------
# BASE BUILD
# -------------------------------
FROM python:3.11-slim AS base

WORKDIR /home/dataline/backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1

RUN apt update && apt install --no-install-recommends libpq5 -y

RUN pip install uv
COPY backend/uv.lock backend/pyproject.toml ./
RUN uv sync --no-dev --no-install-project --compile-bytecode
ENV PATH="/home/dataline/backend/.venv/bin:$PATH"

# Copy backend files (samples dihapus karena folder tidak ada)
COPY backend/*.py .
# COPY backend/samples ./samples          <-- DIHAPUS
COPY backend/dataline ./dataline
COPY backend/alembic ./alembic
COPY backend/templates ./templates
COPY backend/alembic.ini .

WORKDIR /home/dataline
RUN mkdir -p /home/.dataline
ENV SQLITE_PATH="/home/.dataline/db.sqlite3"
ENV DATA_DIRECTORY="/home/.dataline/data"

# -------------------------------
# SPA BUILD WITH MINIMAL DEPS
# -------------------------------
FROM base AS spa

WORKDIR /home/dataline/backend

COPY --from=temp-frontend /home/dataline/frontend/dist /home/dataline/frontend/dist

RUN \
    cp -r /home/dataline/frontend/dist/assets /home/dataline/backend && \
    cp /home/dataline/frontend/dist/favicon.ico /home/dataline/backend/assets && \
    cp /home/dataline/frontend/dist/.vite/manifest.json /home/dataline/backend/assets

ENV SPA_MODE=1

# ⚠️ JANGAN pakai ARG + ENV untuk password/username!
# Biarkan kosong dulu, nanti diatur lewat Environment Variable di EasyPanel
# ARG AUTH_USERNAME
# ENV AUTH_USERNAME=$AUTH_USERNAME
# ARG AUTH_PASSWORD
# ENV AUTH_PASSWORD=$AUTH_PASSWORD

ARG ALLOWED_ORIGINS
ENV ALLOWED_ORIGINS=$ALLOWED_ORIGINS

CMD ["bash", "-c", "python -m dataline.main"]
