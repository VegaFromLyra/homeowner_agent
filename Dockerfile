FROM ghcr.io/openclaw/openclaw:latest

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables ipset iproute2 dnsutils jq dnsmasq \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN npx playwright install --with-deps chromium

COPY init-firewall.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init-firewall.sh

USER node
