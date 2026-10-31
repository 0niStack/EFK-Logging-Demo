# Architecture: what each component does

```
┌────────────┐  stdout   ┌──────────────┐ forward  ┌─────────┐  HTTP   ┌───────────────┐
│ python-app │ ───────▶  │ Docker daemon│ ───────▶ │ Fluentd │ ──────▶ │ Elasticsearch │
│ (logging)  │  JSON     │ fluentd drvr │  :24224  │         │  :9200  │               │
└────────────┘           └──────────────┘          └─────────┘         └───────┬───────┘
                                                                               │
                                                                        ┌──────▼──────┐
                                                                        │   Kibana    │ :5601
                                                                        └─────────────┘
```

## 1. Python app (`app/app.py`)

Produces the logs. It uses the standard `logging` module with a small `JsonFormatter`, so every record is **one JSON line on stdout**:

```json
{"timestamp":"...","level":"ERROR","logger":"demo.app","message":"payment declined",
 "service":"python-demo","env":"dev","request_id":"ab12..","user_id":7,"endpoint":"/payments","status":402}
```

- Extra fields come from `extra={...}` on any log call, with no schema to maintain.
- Exceptions (`log.exception`) become an `exception` field containing the traceback, kept as a single event instead of many lines.
- The app knows nothing about Fluentd or Elasticsearch. It just writes to stdout, which is the 12-factor way.

## 2. Docker fluentd logging driver

Set on the `python-app` service in `docker-compose.yml`. Instead of storing stdout in a local file, the Docker daemon forwards each line to Fluentd at `127.0.0.1:24224` and adds metadata: `container_id`, `container_name`, `source` (stdout/stderr), and the raw line as `log`. The tag is `docker.<container name>`.

## 3. Fluentd (`fluentd/conf/fluent.conf`)

The log router. Config is a pipeline of three stages:

| Stage | Config | What it does here |
|---|---|---|
| **Input** | `<source> @type forward` | Listens on 24224 for the Docker driver |
| **Filter** | `<filter> @type parser` | Parses the JSON string in `log` into real fields |
| **Filter** | `<filter> @type record_transformer` | Adds `fluentd_host` to each event |
| **Output** | `<match> @type elasticsearch` | Writes to Elasticsearch in daily indices `app-logs-YYYY.MM.DD` |

The output has a **file buffer** (`/fluentd/log/buffer`): if Elasticsearch is slow or down, logs queue on disk and are retried with exponential backoff, not lost.

Events are matched by **tag** (`docker.**`), which is how you'd route different services to different outputs.

## 4. Elasticsearch

Stores and indexes the log documents. Each day gets its own index (`app-logs-2026.10.29`), so deleting old data means deleting old indices. Fields are mapped dynamically: `level`, `message`, `endpoint` become searchable; numbers like `duration_ms` and `status` are numeric, so you can aggregate on them.

## 5. Kibana

The UI on top of Elasticsearch. A **data view** (`app-logs-*`, time field `@timestamp`) tells Kibana which indices to read. Then:

- **Discover**: search and filter raw logs (KQL, e.g. `level: "ERROR" and endpoint: "/payments"`)
- **Dashboards / Lens**: charts such as errors over time, p95 `duration_ms`, top endpoints

## Startup order

`elasticsearch` (healthy) → `kibana` and `fluentd` → `python-app`. The log driver is configured with `fluentd-async: true`, so the app starts and buffers logs even if Fluentd is briefly unavailable.
