# Working agreements

- Explain results in Korean unless requested otherwise; keep code identifiers and commands unchanged.
- Read relevant code before editing, follow repository conventions, and keep changes within the requested scope.
- Implement and verify clear, bounded tasks directly. Ask when a missing decision changes behavior or scope. Use a written plan for work spanning sessions or significant dependencies.
- Use skills, agents, and tools for concrete needs; avoid duplicate planning, implementation, and reviews. Give concurrent agents separate worktrees or explicit non-overlapping file ownership.
- Preserve other people's changes, credentials, authentication, permissions, and integration hooks.
- Use the pinned toolchain and existing checks. Start with relevant checks and report checks that could not run.
- Continue authorized work without repeated approval. Ask before publishing, sending messages, destructive changes, or external writes unless already authorized.
- Report changes, verification, and remaining limitations. At a handoff, record the objective, branch/worktree, changed files, verification, and next action.

# Project constraints

- This is a Python font-building CLI, not a web application. `.python-version` selects Python 3.12; use `uv` and the committed `uv.lock`.
- Setup and checks: `uv sync --all-groups`, `make lint`, `make test`, and `make build` (Python package). Font generation uses `make download` followed by `make run`.
- `src/covendard/builder.py` owns font transformations and variant definitions; `src/covendard/cli.py` owns selection and output orchestration; `download_upstream.py` prepares sources.
- Supported Latin sources are `caskaydiacove` (default) and `jetbrainsmono`, using ligature-enabled Nerd Font Mono TTFs. Select with `--latin-family` or Makefile `LATIN_FAMILY`; `--latin-dir` only overrides the source directory.
- CaskaydiaCove defaults to the output family `Covendard`. Support the five same-named Pretendard weights (ExtraLight, Light, Regular, SemiBold, Bold); do not silently approximate SemiLight or synthesize missing weights.
- Preserve the two-cell invariant: copied Korean/CJK advance width equals exactly twice the sampled Latin advance. `--korean-scale` changes outlines, not that advance width, and may be capped per glyph.
- Italic variants use italic Latin and upright Korean/CJK. Keep font names, weight/style metadata, and CSS consistent.
- Preserve the base font's programming ligatures and Nerd Font symbols when modifying GSUB or glyph order.
- `.otf` outputs retain TrueType outlines; do not describe them as CFF conversions.
- Upstream archives and generated fonts are ignored by Git. Do not commit them by default.
- Integration tests require downloaded sources; the full matrix additionally requires `COVENDARD_RUN_FULL_INTEGRATION=1`. Passing helper tests does not establish rendering or shaping correctness.
- Keep `README.md` in Korean and `README.en.md` in English; synchronize user-facing behavior documentation when changing that behavior.

- Covendard CLI defaults to independent Korean x=1.20/y=1.15. `make run` builds the four release styles; `--all` builds ten supported Cove styles.
- CaskaydiaCove integration and Compact spacing are this project author's extensions, not upstream Jetendard variants.
