#!/usr/bin/env bash

set -euo pipefail

NAMESPACE="sourcely"

create_secret() {
    local name="$1"
    local key="$2"

    if sudo k3s kubectl get secret "$name" \
        -n "$NAMESPACE" \
        --ignore-not-found -o name | grep -q .; then

        echo "Secret $name already exists. Skipping."
    else
        openssl rand -hex 32 | tr -d '\n' | \
            sudo k3s kubectl create secret generic "$name" \
                --namespace="$NAMESPACE" \
                --from-file="$key=/dev/stdin"
    fi
}

# Authenticate Agent-to-Sandbox requests
create_secret "sandbox-secret" "SANDBOX_API_KEY"

# SearXNG internal secret key
create_secret "searxng-secret" "SEARXNG_SECRET"

echo "Secret initialization completed."