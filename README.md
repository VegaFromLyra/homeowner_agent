# Homeowner Agent

A Docker-based homeowner agent built on the [OpenClaw](https://docs.openclaw.ai) framework with Playwright/Chromium for browser automation.

## Prerequisites

- Docker and Docker Compose
- An Anthropic API key

## Setup

1. Create a `.env` file at the project root:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```

2. Build and start the container:
   ```bash
   docker compose up --build -d
   ```

## Starting OpenClaw

1. Open a shell in the running container:
   ```bash
   docker compose exec openclaw bash
   ```

2. Run the onboarding flow:
   ```bash
   openclaw onboard
   ```

3. Launch the dashboard:
   ```bash
   openclaw dashboard
   ```

   The dashboard will be available at `http://localhost:18789`.
