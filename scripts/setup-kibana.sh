#!/usr/bin/env bash
# Creates the Kibana data view for the app-logs-* indices (idempotent).
set -euo pipefail

KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"
PATTERN="${INDEX_PATTERN:-app-logs-*}"

echo "Waiting for Kibana at ${KIBANA_URL} ..."
until curl -sf "${KIBANA_URL}/api/status" | grep -q '"level":"available"'; do
  sleep 3
done

echo "Creating data view '${PATTERN}' ..."
code=$(curl -s -o /tmp/kibana_dv.json -w '%{http_code}' -X POST "${KIBANA_URL}/api/data_views/data_view" \
  -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
  -d "{\"data_view\":{\"title\":\"${PATTERN}\",\"name\":\"app-logs\",\"timeFieldName\":\"@timestamp\"}}")

if [[ "$code" == "200" ]]; then
  echo "Created."
elif grep -qi "duplicate" /tmp/kibana_dv.json; then
  echo "Data view already exists, nothing to do."
else
  echo "Unexpected response ($code):"; cat /tmp/kibana_dv.json; exit 1
fi

echo "Open: ${KIBANA_URL}/app/discover"
