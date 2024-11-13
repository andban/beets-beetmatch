.PHONY: format install-dev install lint test

format:
	@command -v ruff >/dev/null || python -m pip install '.[dev]'
	python -m ruff format .

lint:
	@command -v ruff >/dev/null || python -m pip install '.[dev]'
	python -m ruff check .

install:
	python -m pip install .

install-dev:
	python -m pip install -e '.[dev]'

test:
	pytest --cov='beetsplug.beetmatch'