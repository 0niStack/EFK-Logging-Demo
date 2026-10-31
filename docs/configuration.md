# Configuration guide

Most knobs live in `.env`; pipeline logic lives in `fluentd/conf/fluent.conf`. After changing `.env` or compose, run `make up`. After changing `fluent.conf`, run `docker compose restart fluentd`.

## 1. Python app

| Variable (`.env`) | Default | Meaning |
|---|---|---|
| `SERVICE_NAME` | `python-demo` | Added to every log as `service`; use it to filter in Kibana |
| `APP_ENV` | `dev` | Added as `env` |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR`. Set `DEBUG` to see the cache-miss logs |
| `LOG_INTERVAL` | `1.0` | Seconds between simulated requests |

**Using this in your own app**: copy `JsonFormatter` and `setup_logging()` from `app/app.py`, then:

```python
log = logging.getLogger("myapp")
log.info("order created", extra={"order_id": 42, "user_id": 7})
```

Keep field types stable (don't log `user_id` as an int in one place and a string in another), because Elasticsearch fixes a field's type per index and rejects conflicts.

## 2. Docker log driver (`docker-compose.yml`)

Add this block to **any** service to ship its logs:

```yaml
logging:
  driver: fluentd
  options:
    fluentd-address: 127.0.0.1:24224
    fluentd-async: "true"
    tag: docker.{{.Name}}
```

| Option | Purpose |
|---|---|
| `fluentd-address` | Where the Docker daemon finds Fluentd (host-published port) |
| `fluentd-async` | Don't block/fail container start if Fluentd is down |
| `fluentd-max-retries` / `fluentd-retry-wait` | Reconnect behaviour |
| `tag` | Routing tag; must match `<filter>`/`<match>` patterns in `fluent.conf` |

If your service logs plain text (not JSON), the parser filter keeps the line as-is in the `log` field.

## 3. Fluentd (`fluentd/conf/fluent.conf`)

**Parser filter**: `key_name log` is the field holding the raw line; `reserve_data true` keeps Docker's metadata; change `@type json` to `regexp` or `nginx` to parse other formats.

**Add or modify fields** (`record_transformer`):
```
<record>
  team "platform"
</record>
```

**Drop noisy logs** (add before the output):
```
<filter docker.**>
  @type grep
  <exclude>
    key level
    pattern /DEBUG/
  </exclude>
</filter>
```

**Elasticsearch output**:

| Setting | Meaning |
|---|---|
| `logstash_prefix` | Index name prefix (`ES_INDEX_PREFIX` env). Index = `<prefix>-YYYY.MM.DD` |
| `flush_interval` | How often the buffer is sent. Lower = fresher logs, more requests |
| `chunk_limit_size` | Max buffer chunk size |
| `retry_forever` | Keep retrying instead of discarding when ES is down |
| `host` / `port` / `scheme` | Elasticsearch endpoint |

**Routing different services to different indices**: give each service its own tag (e.g. `docker.billing`) and add a second `<match docker.billing>` block with a different `logstash_prefix`, placed *before* the generic `<match docker.**>`.

**Extra plugins**: add `gem install fluent-plugin-xyz` lines to `fluentd/Dockerfile` and rebuild.

## 4. Elasticsearch

| Setting | Where | Notes |
|---|---|---|
| Version | `ELASTIC_VERSION` in `.env` | Keep Elasticsearch and Kibana on the same version |
| Heap | `ES_HEAP` in `.env` | Rule of thumb: half of the container's RAM, max ~31g |
| Single node | `discovery.type=single-node` | Remove for a real cluster |
| Security | `xpack.security.enabled=false` | **Demo only** |

**Retention** (delete indices older than N days). Simplest manual form:
```bash
curl -X DELETE 'localhost:9200/app-logs-2026.10.01'
```
For automatic cleanup, create an Index Lifecycle Management (ILM) policy with a delete phase (Kibana → Stack Management → Index Lifecycle Policies) and attach it to the `app-logs-*` template.

## 5. Kibana

- Data view: `make setup` creates `app-logs-*` with time field `@timestamp`. Override with `INDEX_PATTERN=other-* ./scripts/setup-kibana.sh`.
- Useful KQL queries: `level: "ERROR"`, `status >= 500`, `duration_ms > 1000`, `endpoint: "/payments" and user_id: 7`
- Add columns (`level`, `message`, `endpoint`, `duration_ms`) in Discover, then **Save** the search.

## Going to production

- Enable security: `xpack.security.enabled=true`, set passwords, use a service account/API key in Fluentd's `user`/`password` (or `api_key`) and HTTPS (`scheme https`, `ca_file`).
- Run a 3-node Elasticsearch cluster with persistent volumes and snapshots.
- Put Kibana behind a reverse proxy with TLS and authentication.
- Run Fluentd as a daemonset/agent per host (or use Fluent Bit as the agent and Fluentd as an aggregator).
- Pin all image versions and set up ILM for retention.
