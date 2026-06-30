.PHONY: install playground run test

install:
	uv sync

playground:
	uv run adk web ecochain --host 127.0.0.1 --port 18081 --reload_agents

run:
	uv run python -m ecochain.server

test:
	uv run python -m unittest tests/test_system.py
