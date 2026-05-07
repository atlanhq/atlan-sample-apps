.PHONY: generate check-generate

generate:
	pkl eval --project-dir contract -m app/generated contract/app.pkl

check-generate: generate
	@git diff --exit-code app/generated/ \
		|| (echo "ERROR: Generated files are stale. Run 'make generate' and commit." && exit 1)
