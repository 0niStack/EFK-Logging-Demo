# EFK + Python logging demo

A self-contained **Elasticsearch + Fluentd + Kibana** stack with a small **Python app** that writes structured JSON logs. Everything runs in Docker Compose.

```
python-app ──stdout (JSON)──▶ Docker fluentd log driver ──▶ Fluentd ──▶ Elasticsearch ◀── Kibana
```

## Quick start

```bash
make up        # build + start (first run pulls ~1.5 GB of images)
make setup     # create the Kibana data view (app-logs-*)
```

Then open **http://localhost:5601 → Analytics → Discover**. Logs appear within ~10 seconds.

Useful commands:

| Command | What it does |
|---|---|
| `make status` | Container state + Elasticsearch indices |
| `make count` | Number of log documents stored |
| `make logs` | Follow Fluentd output |
| `make down` | Stop (keeps data) |
| `make clean` | Stop and delete all data |

Quick API check: `curl 'localhost:9200/app-logs-*/_search?q=level:ERROR&size=2&pretty'`

> **Linux host:** Elasticsearch needs `vm.max_map_count >= 262144`: `sudo sysctl -w vm.max_map_count=262144`

## Project layout

```
.
├── docker-compose.yml        # the 4 services
├── .env                      # versions + app settings
├── Makefile
├── app/                      # Python demo app (Dockerfile + app.py)
├── fluentd/
│   ├── Dockerfile            # Fluentd + Elasticsearch plugin
│   └── conf/fluent.conf      # pipeline: input → filter → output
├── scripts/setup-kibana.sh   # creates the Kibana data view
└── docs/
    ├── architecture.md       # what each component does
    ├── configuration.md      # how to configure each component
    └── troubleshooting.md
```

## Docs

- [docs/architecture.md](docs/architecture.md): what each piece does and how data flows
- [docs/configuration.md](docs/configuration.md): every setting worth changing
- [docs/troubleshooting.md](docs/troubleshooting.md): common problems

**Demo only:** security is disabled and Elasticsearch runs as a single node. See "Going to production" in `docs/configuration.md`.
