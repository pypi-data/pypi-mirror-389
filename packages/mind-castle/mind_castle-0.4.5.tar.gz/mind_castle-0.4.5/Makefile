install:
	pip install uv
	uv sync --frozen

install_dev:
	pip install uv
	uv sync --frozen --dev

test:
	uv run --frozen pytest -v

lint:
	uv run --frozen ruff format
	uv run --frozen ruff check

build:
	uv build --frozen

# NOTE: You need to set UV_PUBLISH_TOKEN in your terminal
publish:
	uv build --frozen
	uv publish --frozen

# Update all the depends in the lockfile to the latest versions
update-depends:
	uv sync --refresh

.PHONY: install install_dev precommit test lint build update-depends
