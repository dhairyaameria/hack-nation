.PHONY: dev dev-api dev-web dev-web-alt db-reset db-seed mcp pipeline inbound-rerank

# Run API (:8000) + web (:3000) together. Ctrl-C stops both.
dev:
	@echo "API  → http://127.0.0.1:8000"
	@echo "Web  → http://127.0.0.1:3000  (if busy: make dev-web-alt)"
	@trap 'kill 0' EXIT; \
	$(MAKE) --no-print-directory dev-api & \
	$(MAKE) --no-print-directory dev-web & \
	wait

dev-api:
	cd apps/api && source .venv/bin/activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000

dev-web:
	cd apps/web && npm run dev -- --port 3000

# Use when something else already owns :3000
dev-web-alt:
	cd apps/web && npm run dev -- --port 3001

# Dev only — requires DATABASE_URL or Supabase connection in .env
db-reset:
	@echo "Apply migrations in order — see docs/16-MIGRATIONS-GUIDE.md"
	@for f in db/migrations/*.sql; do \
		echo "Applying $$f..."; \
		psql "$$DATABASE_URL" -f "$$f" || exit 1; \
	done

db-seed:
	cd apps/api && source .venv/bin/activate && python ../../db/seed/seed.py

# MCP server (stdio): agents' entry point to the memory layer, see docs/18-MEMORY-LAYER.md
mcp:
	cd apps/api && source .venv/bin/activate && python -m api.mcp.server

# Product 2 daily loop: screens/analyzes seeded opportunities, see jobs/pipelines/
pipeline:
	cd apps/api && source .venv/bin/activate && python ../../jobs/pipelines/daily_pipeline.py

# Perplexity inbound rerank (same code path as POST /api/v1/inbound/rerank)
inbound-rerank:
	cd apps/api && source .venv/bin/activate && PYTHONPATH=. python ../../jobs/pipelines/inbound_rerank_cron.py
