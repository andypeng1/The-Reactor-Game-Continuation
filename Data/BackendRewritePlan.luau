return [[
Backend rewrite started 2026-09-25.

Phase 1: create a shadow runtime in ServerScriptService.ReactorBackend.
Phase 2: migrate shared state and shift lifecycle behind compatibility adapters.
Phase 3: migrate control dispatch and validate every control against legacy behavior.
Phase 4: migrate simulation systems one writer at a time.
Phase 5: remove legacy writers only after play-mode verification.

ServerStorage.Data was inspected: TRGWeb is the legacy HTML reference model,
Summary01 is the video/gameplay summary, DataCollection is a telemetry script,
and DataCollection.Log is historical JSONL data rather than executable backend code.
]]
