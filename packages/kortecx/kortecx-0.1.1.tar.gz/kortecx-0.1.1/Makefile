rusty:
	cd backend && uv run maturin develop

run-checks:
	ruff check --fix
	black .

checkout:
	git pull origin main
	git checkout $(branch)

build:
	rm -rf dist
	rm -rf src/kortecx/frontend/node_modules
	uv build
	cd src/kortecx/frontend && npm i