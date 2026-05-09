# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Docker-based homeowner agent built on the [OpenClaw](https://docs.openclaw.ai) framework with Playwright/Chromium for browser automation. The agent uses the Anthropic API (Claude) and interacts with home services platforms like Angi.

## Development Commands

```bash
# Build and start the container
docker compose up --build -d

# View logs
docker compose logs -f

# Stop the container
docker compose down

# Rebuild after Dockerfile changes
docker compose build --no-cache
```

## Architecture

- **Base image**: `ghcr.io/openclaw/openclaw:latest` — provides the OpenClaw agent runtime (Node.js)
- **Playwright + Chromium**: Installed on top of the base image for browser automation tasks
- **OpenClaw UI**: Accessible at `http://localhost:18789` when the container is running
- **Workspace mount**: Current directory is mounted to `/app/workspace` inside the container
- **OpenClaw config**: `.openclaw/` directory is mounted to `/home/node/.openclaw` for persistent runtime state

## Environment Setup

Requires a `.env` file at the project root with:
- `ANTHROPIC_API_KEY` — API key for Claude

## Key Files

- `Dockerfile` — Container definition (extends OpenClaw base with Playwright)
- `docker-compose.yml` — Service orchestration, volume mounts, port mapping
- `.openclaw/openclaw.json` — OpenClaw runtime configuration (token auth, UI settings)
