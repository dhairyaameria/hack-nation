.PHONY: dev-api dev-web db-reset db-seed mcp pipeline

dev-api:
	cd apps/api && source .venv/bin/activate && uvicorn main:app --reload --port 8000

dev-web:
	cd apps/web && npm run dev

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
