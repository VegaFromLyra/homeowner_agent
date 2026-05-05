#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Allowed domains — dnsmasq will auto-add resolved IPs to the ipset
ALLOWED_DOMAINS=(
    "api.anthropic.com"
    "sentry.io"
    "statsig.anthropic.com"
    "statsig.com"
    "angi.com"
    "www.angi.com"
    "api.angi.com"
    "request.angi.com"
    "lpfe-static-assets.angi.com"
    "cdn.playwright.dev"
    "playwright.download.prss.microsoft.com"
    "sdk.split.io"
    "auth.split.io"
)

# 1. Extract Docker DNS info BEFORE any flushing
DOCKER_DNS_RULES=$(iptables-save -t nat | grep "127\.0\.0\.11" || true)
# Get Docker's upstream DNS server
DOCKER_DNS=$(grep nameserver /etc/resolv.conf | head -1 | awk '{print $2}')

# Flush existing rules and delete existing ipsets
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X
ipset destroy allowed-domains 2>/dev/null || true

# 2. Restore Docker DNS resolution
if [ -n "$DOCKER_DNS_RULES" ]; then
    echo "Restoring Docker DNS rules..."
    iptables -t nat -N DOCKER_OUTPUT 2>/dev/null || true
    iptables -t nat -N DOCKER_POSTROUTING 2>/dev/null || true
    echo "$DOCKER_DNS_RULES" | xargs -L 1 iptables -t nat
else
    echo "No Docker DNS rules to restore"
fi

# Allow DNS (to Docker's DNS and localhost for dnsmasq)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p udp --sport 53 -j ACCEPT
iptables -A INPUT -p udp --dport 53 -j ACCEPT
# Allow SSH
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT
# Allow localhost
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Create ipset for allowed domains
ipset create allowed-domains hash:ip

# 3. Configure dnsmasq as local DNS proxy with ipset integration
# Every DNS lookup for an allowed domain automatically adds the resolved IP to the ipset
DNSMASQ_CONF="/etc/dnsmasq.d/firewall.conf"
mkdir -p /etc/dnsmasq.d

{
    echo "# Forward to Docker's upstream DNS"
    echo "server=${DOCKER_DNS}"
    echo "no-resolv"
    echo "listen-address=127.0.0.1"
    echo "bind-interfaces"
    echo "cache-size=1000"
    echo ""
    echo "# Auto-add resolved IPs to ipset for allowed domains"
    for domain in "${ALLOWED_DOMAINS[@]}"; do
        echo "ipset=/${domain}/allowed-domains"
    done
} > "$DNSMASQ_CONF"

# Start dnsmasq
echo "Starting dnsmasq..."
dnsmasq --conf-file="$DNSMASQ_CONF"

# Point the container's DNS at local dnsmasq
echo "nameserver 127.0.0.1" > /etc/resolv.conf

# 4. Seed the ipset by resolving all domains once through dnsmasq
for domain in "${ALLOWED_DOMAINS[@]}"; do
    echo "Seeding $domain..."
    dig +noall +answer A "$domain" @127.0.0.1 > /dev/null 2>&1 || true
done

echo "Seeded ipset with $(ipset list allowed-domains | grep -c '^[0-9]' || echo 0) IPs"

# Allow host network (for Docker-to-host communication)
HOST_IP=$(ip route | grep default | cut -d" " -f3)
if [ -n "$HOST_IP" ]; then
    HOST_NETWORK=$(echo "$HOST_IP" | sed "s/\.[0-9]*$/.0\/24/")
    echo "Host network detected as: $HOST_NETWORK"
    iptables -A INPUT -s "$HOST_NETWORK" -j ACCEPT
    iptables -A OUTPUT -d "$HOST_NETWORK" -j ACCEPT
fi

# Set default policies to DROP
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow outbound to allowlisted IPs only
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT

# Reject everything else with immediate feedback
iptables -A OUTPUT -j REJECT --reject-with icmp-admin-prohibited

echo "Firewall configuration complete (dnsmasq-backed)"

# Verify: blocked domain should fail
if curl --connect-timeout 5 https://example.com >/dev/null 2>&1; then
    echo "ERROR: Firewall verification failed - able to reach example.com"
    exit 1
else
    echo "Firewall verified - example.com blocked as expected"
fi

# Verify: allowed domain should succeed
if curl --connect-timeout 5 https://angi.com >/dev/null 2>&1; then
    echo "Firewall verified - angi.com reachable as expected"
else
    echo "WARNING: angi.com not reachable, DNS IPs may have changed"
fi
