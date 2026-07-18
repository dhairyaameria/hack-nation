.PHONY: dev-api dev-web db-reset db-seed

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
