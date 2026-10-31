.PHONY: up setup down logs status count clean

up:       ## Build and start the stack
	docker compose up -d --build

setup:    ## Create the Kibana data view (run after `make up`)
	./scripts/setup-kibana.sh

down:     ## Stop the stack (keeps data)
	docker compose down

logs:     ## Follow fluentd output
	docker compose logs -f fluentd

status:   ## Container + index status
	docker compose ps
	@curl -s 'http://localhost:9200/_cat/indices/app-logs-*?v' || true

count:    ## Number of log documents in Elasticsearch
	@curl -s 'http://localhost:9200/app-logs-*/_count?pretty'

clean:    ## Stop and delete all data
	docker compose down -v
