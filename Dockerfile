FROM ghcr.io/openclaw/openclaw:latest

USER root
RUN npx playwright install --with-deps chromium
USER node
