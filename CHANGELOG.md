# Changelog

All notable changes to **Dev Context Engine (DCE)** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Nothing yet (post 1.13.0).

## [1.13.0] - 2026-07-29

### Added

- PB-071: MCP tool `search_by_project` — typed alias scoping `search_context` to a project slug (`payments` / `project:payments`).

### Notes

- Additive to MCP `schema_version` `"1"`; contract freeze updated.

## [1.12.0] - 2026-07-29

### Added

- PB-096: Git bootstrap + `scripts/cut_release.sh` (annotated SemVer tag aligned to package version; optional `--push`).

### Notes

- Docs: [`docs/ReleaseGit.md`](docs/ReleaseGit.md).
- Pushing tags is still a maintainer action (configure `origin` first).

## [1.11.0] - 2026-07-29

### Added

- PB-095: Windows portable release automation — SHA-256 checksum beside the ZIP; GitHub Release assets on `v*` tags.

### Notes

- Docs: [`docs/ReleaseWindows.md`](docs/ReleaseWindows.md).
- `workflow_dispatch` still uploads CI artifacts without creating a Release.

## [1.10.0] - 2026-07-29

### Added

- PB-094: Windows portable `dce.exe` ZIP packaging (PyInstaller onefile + PowerShell script + GitHub Actions workflow).

### Notes

- Build runs on Windows only (`windows-latest` CI or local PowerShell). Not cross-compiled from macOS/Linux.
- Docs: [`docs/Windows.md`](docs/Windows.md).

## [1.9.0] - 2026-07-29

### Added

- PB-070: MCP tool `search_by_issue` — typed alias for Jira-like keys (`PAY-125` / `issue:PAY-125`).

### Notes

- MCP `schema_version` remains `"1"` (additive tool).
- Evidence: QueryKind.ISSUE, jira indexer, `related_uris` `issue:` links.

## [1.8.0] - 2026-07-29

### Added

- PB-092: optional git `post-commit` hook via `dce hooks install|uninstall|status` (soft-fail `dce index --source git`).
- `dce doctor` reports `git_hook` when `.git` is present.

### Notes

- Hook is opt-in; never overwrites foreign hooks without `--force`.
- Index failures never fail the git commit.

## [1.7.0] - 2026-07-29

### Added

- PB-012: structured logging (stdlib) — JSON Lines or text on stderr; CLI `--verbose` / `--log-format`; env `DCE_LOG_LEVEL` / `DCE_LOG_FORMAT`.

### Notes

- MCP keeps stdout clean; logs always go to stderr.
- PB-011 marked complete (CI workflow already present).

## [1.6.0] - 2026-07-29

### Added

- PB-080 (thin): optional `jira_rest` indexer — JQL search via Jira REST API v2; credentials from env only; network/auth failures skip (offline-safe).

### Notes

- Disabled by default. Enable in `dce.yaml` and set `JIRA_BASE_URL` + (`JIRA_EMAIL`/`JIRA_API_TOKEN` or `JIRA_PAT`).
- Reuses `normalize_issue` / Document shape from `jira_import` (`source_type=jira`).

## [1.5.0] - 2026-07-29

### Added

- PB-083: Snippet indexer (`source_type=snippet`) for curated code/command notes under `.dce/snippets/**`, `snippets/**`, `docs/snippets/**`.

### Notes

- Extracts language/code from frontmatter or the first fenced code block.
- Planner prefers snippets for ERROR_CODE and PATH queries.

## [1.4.0] - 2026-07-29

### Added

- PB-082: Incident indexer (`source_type=incident`) for typed markdown postmortems under `.dce/incidents/**`, `incidents/**`, `docs/incidents/**`.

### Notes

- Enabled by default; markdown indexer excludes incident paths.
- Frontmatter: severity, status, impact, resolution, root_cause, error_codes, timeline fields.

## [1.3.0] - 2026-07-29

### Added

- PB-081: Procedure indexer (`source_type=procedure`) for typed markdown runbooks under `.dce/procedures/**`, `procedures/**`, `docs/procedures/**`.

### Notes

- Enabled by default; markdown indexer excludes procedure paths.
- Extracts `steps` from frontmatter or numbered/checkbox body lines.

## [1.2.0] - 2026-07-29

### Added

- PB-051: canonical `related_uris` (`issue:`, `commit:`, `pr:` / HTTPS) plus post-index bidirectional linker (jira ↔ git ↔ PR).

### Notes

- Paths in `related_uris` stay bare for backward compatibility.
- Linker processes up to 500 documents per source type per `dce index` run.

## [1.1.0] - 2026-07-29

### Added

- MCP tool `search_memory` — typed alias over `search_context` with `source_type=memory` (PB-032).
- Publish automation: `scripts/publish.sh` and GitHub Actions `publish.yml` (workflow_dispatch).

### Notes

- MCP `schema_version` remains `"1"` (additive tool).
- PyPI upload still requires `PYPI_TOKEN` / repo secret.

## [1.0.0] - 2026-07-29

### Added

- First stable release: MCP `schema_version: "1"` contract freeze.
- Production/Stable PyPI classifier; distribution `dev-context-engine`.
- Bench evidence for synthetic 500-doc corpus ([`docs/bench-results/`](docs/bench-results/)).

### Notes

- Runtime surface matches `1.0.0rc1` (no intentional breaking changes).
- PyPI upload and Git tag remain maintainer actions (see Release Checklist).
- Out of scope for 1.0: Jira REST live, `search_by_*` aliases, vector search.

## [1.0.0rc1] - 2026-07-29

### Added

- First 1.0 release candidate: MCP schema_version 1 freeze + release checklist.
- PyPI classifier moved to Beta; packaging remains `dev-context-engine`.

### Notes

- Not yet published to PyPI (maintainer token required).
- Final `1.0.0` follows [`docs/ReleaseChecklist-1.0.md`](docs/ReleaseChecklist-1.0.md).
- No intentional breaking changes vs `0.12.0a1` runtime behavior.

## [0.12.0a1] - 2026-07-29

### Added

- `dce backup` / `dce restore` — WAL-safe SQLite snapshot via online backup API.
- Optional JSON manifest sidecar with schema/version metadata.

## [0.11.0a1] - 2026-07-29

### Added

- `dce bench` — synthetic latency benchmark (build/search/get) with p50/p95/p99.
- Documented SLO registry (`docs/SLOs.md`) and operations runbook (`docs/Operations.md`).

### Notes

- Bench corpus is synthetic/directional; do not hard-fail CI on `within_slo`.
- SemVer `1.0.0` still gated on publish + field evidence.

## [0.10.0a1] - 2026-07-29

### Added

- Configurable anchor dictionary (`retrieval.anchors.extra_patterns` in `dce.yaml`).
- Built-in issue / ORA / path patterns remain; extras merge or replace by `name`.
- Anchor `kind` drives QueryKind classification (error_code / issue / path / …).

## [0.9.0a1] - 2026-07-29

### Added

- PyPI packaging readiness: distribution name `dev-context-engine` (CLI/import remain `dce`).
- Hatch wheel/sdist build fixed (removed broken `force-include`).
- `docs/Packaging.md`, ADR-005, CI build + twine + wheel smoke.
- Classifiers, project URLs, `build`/`twine` in `[dev]` extras.

### Notes

- Upload to PyPI remains a manual maintainer step (credentials).
- Name `dce` on PyPI is taken by an unrelated placeholder package.

## [0.8.0a1] - 2026-07-29

### Added

- Normative MCP contract docs (`docs/MCP.md`) and ADR-004 (schema_version 1 stability).
- Shared MCP contract constants (`dce.interfaces.mcp.contract`).
- Stronger MCP contract tests (tool freeze, diagnostics keys, empty-query shape).
- Kiro MCP registration example in README.

### Notes

- Still pre-1.0: packaging/SLOs remain for later sprints.
- Tool surface frozen at four tools; aliases stay evidence-gated.

## [0.7.0a1] - 2026-07-29

### Added

- Built-in technical synonym dictionary with `retrieval.synonyms` overrides in `dce.yaml`.
- Synonym expansion as extra FTS retrieval steps in the planner.
- Richer `RetrievalDiagnostics`: `query_kind`, `preferred_sources`, `steps`, `synonym_expansions`.

### Notes

- Diagnostics fields are additive; MCP `schema_version` stays `1`.
- User `source_types` filters still suppress preferred-source steps.

## [0.6.0a1] - 2026-07-29

### Added

- Query-kind classification in RetrievalPlanner (`error_code`, `issue`, `architecture`, `path`, `general`).
- Preferred-source retrieval steps per query kind (precision passes).
- Ranking boosts: title/anchor/tags, preferred-source weight, freshness (0..2).
- Semantic section names (e.g. `similar_bugs`, `adrs`, `related_commits`).

### Notes

- User-provided `source_types` filters still win (no preferred-source override).

## [0.5.0a1] - 2026-07-29

### Added

- Conservative Git indexer.

## [0.4.0a1] - 2026-07-29

### Added

- Offline Jira import (JSON/CSV).

## [0.3.0a1] - 2026-07-29

### Added

- ADR and Memory indexers.

## [0.2.0a1] - 2026-07-29

### Added

- MCP stdio server for Kiro.

## [0.1.0a3] / [0.1.0a2] / [0.1.0a1] / [0.0.0]

- Earlier foundation releases (store, markdown, context builder).

[Unreleased]: https://github.com/adrianobotelho/DCE/compare/v1.13.0...HEAD
[1.13.0]: https://github.com/adrianobotelho/DCE/compare/v1.12.0...v1.13.0
[1.12.0]: https://github.com/adrianobotelho/DCE/compare/v1.11.0...v1.12.0
[1.11.0]: https://github.com/adrianobotelho/DCE/compare/v1.10.0...v1.11.0
[1.10.0]: https://github.com/adrianobotelho/DCE/compare/v1.9.0...v1.10.0
[1.9.0]: https://github.com/adrianobotelho/DCE/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/adrianobotelho/DCE/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/adrianobotelho/DCE/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/adrianobotelho/DCE/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/adrianobotelho/DCE/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/adrianobotelho/DCE/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/adrianobotelho/DCE/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/adrianobotelho/DCE/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/adrianobotelho/DCE/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/adrianobotelho/DCE/compare/v1.0.0rc1...v1.0.0
[1.0.0rc1]: https://github.com/adrianobotelho/DCE/compare/v0.12.0a1...v1.0.0rc1
[0.12.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.11.0a1...v0.12.0a1
[0.11.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.10.0a1...v0.11.0a1
[0.10.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.9.0a1...v0.10.0a1
[0.9.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.8.0a1...v0.9.0a1
[0.8.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.7.0a1...v0.8.0a1
[0.7.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.6.0a1...v0.7.0a1
[0.6.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.5.0a1...v0.6.0a1
[0.5.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.4.0a1...v0.5.0a1
[0.4.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.3.0a1...v0.4.0a1
[0.3.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.2.0a1...v0.3.0a1
[0.2.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.1.0a3...v0.2.0a1
[0.1.0a3]: https://github.com/adrianobotelho/DCE/compare/v0.1.0a2...v0.1.0a3
[0.1.0a2]: https://github.com/adrianobotelho/DCE/compare/v0.1.0a1...v0.1.0a2
[0.1.0a1]: https://github.com/adrianobotelho/DCE/compare/v0.0.0...v0.1.0a1
[0.0.0]: https://github.com/adrianobotelho/DCE/releases/tag/v0.0.0
