# Troubleshooting

| Symptom | Check / fix |
|---|---|
| Elasticsearch exits immediately (Linux) | `sudo sysctl -w vm.max_map_count=262144` |
| Elasticsearch OOM-killed | Lower `ES_HEAP` in `.env` or give Docker more RAM (needs ~2 GB total) |
| No logs in Kibana | See the checklist below |
| `make setup` hangs | Kibana takes ~1 min to start; check `docker compose logs kibana` |
| `python-app` fails to start: cannot connect to fluentd | Make sure port 24224 is published and nothing else uses it: `ss -ltn | grep 24224` |
| Fields show as `log` string, not parsed | App output isn't valid JSON per line; run `docker compose logs fluentd` and look for parse warnings |
| `mapper_parsing_exception` in Fluentd log | A field changed type (e.g. int → string). Keep types consistent or use a new index |

## "No logs" checklist

1. Containers healthy? `make status`
2. App is producing? `docker compose exec python-app true` (it's running) and see the JSON via Fluentd's own output: `docker compose logs --tail 20 fluentd`
3. Documents in Elasticsearch? `make count`; if count is 0, check Fluentd for `retry` / `connection refused` errors
4. Data view exists with time field `@timestamp`, and Kibana's time range (top right) is "Last 15 minutes"

Note: `docker logs efk-python-app` will be **empty** when the fluentd log driver is used. The logs are in Elasticsearch, not in Docker's local store.
