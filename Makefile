.PHONY: dev lint format test build download ensure-upstream run run-all run-minimal clean

LATIN_FAMILY ?= jetbrainsmono

dev:
	uv sync --all-groups

lint:
	uv run ruff format --check .
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

build:
	uv build

download:
	uv run python download_upstream.py --latin-family $(LATIN_FAMILY)

ensure-upstream:
	uv run python download_upstream.py --latin-family $(LATIN_FAMILY) --ensure

run: ensure-upstream
	uv run jetendard --latin-family $(LATIN_FAMILY) --all

run-all: ensure-upstream
	uv run jetendard --latin-family $(LATIN_FAMILY) --all

run-minimal: ensure-upstream
	uv run jetendard --latin-family $(LATIN_FAMILY) --variants Regular Light Bold

clean:
	rm -rf fonts/ttf fonts/otf fonts/webfont fonts/specimens
