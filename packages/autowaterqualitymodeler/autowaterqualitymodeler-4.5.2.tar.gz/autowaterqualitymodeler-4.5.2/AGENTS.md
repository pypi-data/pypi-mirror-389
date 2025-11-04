# Repository Guidelines

## 语言与沟通
- 始终用中文回答问题（除非用户明确要求使用其他语言）。
- 代码标识符、命令、路径与对外接口名称保持英文；文档与注释默认中文。
- PR 描述与提交说明优先中文，可附英文对照。

## Project Structure & Module Organization
- Source code lives in `autowaterqualitymodeler/`:
  - `core/` (data structures, config, validators, exceptions)
  - `features/` (feature calculations), `models/` (builders), `preprocessing/` (spectrum)
  - `cli/` (entrypoints), `utils/` (logging, cache, parallel, encryption)
  - `resources/` (CIE tables), `config/` (JSON configs + README)
- Tests in `tests/`; `test_20250804/` contains exploratory scripts not used in CI.
- Example scripts: `comprehensive_demo.py`, `example_real_data.py`, `analyze_results.py`.
- Sample data: `data/`.

## Build, Test, and Development Commands
- Install (editable dev): `python -m pip install -e .`
- Run CLI help: `python -m autowaterqualitymodeler.cli.main --help`
- Example predict: `python -m autowaterqualitymodeler.cli.main predict --config autowaterqualitymodeler\config\system_config.json`
- Demos: `python comprehensive_demo.py` or `python example_real_data.py`
- Tests (all/targeted): `pytest -q` or `pytest tests/test_modeler.py -q`

## Coding Style & Naming Conventions
- Follow PEP 8; 4-space indentation; prefer type hints and concise docstrings.
- Names: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Keep domain logic in `core/`, deterministic transforms in `features/`/`preprocessing/`, orchestration in `cli/`.
- Logging via `utils/logger.py`; avoid print in library code.

## Testing Guidelines
- Framework: `pytest` (config in `pytest.ini`). Tests under `tests/` named `test_*.py`.
- Add fixtures to `tests/conftest.py`; prefer small, deterministic inputs.
- Aim for 80%+ coverage on touched code; include edge cases (empty/NaN spectra, invalid config, I/O errors).

## Commit & Pull Request Guidelines
- Use Conventional Commit prefixes seen in history: `feat:`, `fix:`, `refactor:`, `update:`, `publish:` (en/zh acceptable). Keep subjects imperative and ≤72 chars.
- PRs must include: clear description, linked issues, before/after or CLI example, tests for changes, and updates to `autowaterqualitymodeler/config/` or docs when applicable.
- Ensure `pytest -q` passes and examples run.

## Security & Configuration Tips
- Keep secrets out of VCS; edit JSON in `autowaterqualitymodeler\config\` thoughtfully and document defaults.
- Treat `resources/` as read-only unless updating source data; prefer relative paths.
- For reproducibility, use pinned deps from `pyproject.toml`/`uv.lock`. Optional: `uv sync`, `uv run pytest` if using `uv`.
