# Session Handoff Readiness Standard

Last updated: 2026-02-21

Purpose:
- verify that a new Codex session can follow `CODEX_SESSION_GUIDE.md` end-to-end;
- ensure mandatory read chain and key completion references are present and linked;
- produce explicit handoff audit artifacts.

## Script

- `scripts/check_session_handoff_readiness.py`

## Standard Usage

```bash
python scripts/check_session_handoff_readiness.py
```

## Outputs

- `audit/session_handoff/handoff_readiness.json`
- `audit/session_handoff/handoff_readiness.md`

## Checks

1. Parse Section 3 in `CODEX_SESSION_GUIDE.md` and extract mandatory read sequence.
2. Verify each mandatory read path exists.
3. Verify each mandatory read path is linked in `DOCS_INDEX.md`.
4. Parse completion-check referenced paths in Section 3 and verify they exist.
5. Record completion-check path linkage status in `DOCS_INDEX.md` for audit visibility.

## Pass Criteria

`overall_pass = true` only if:
1. mandatory read sequence is non-empty
2. no missing mandatory-read files
3. no unlinked mandatory-read files in `DOCS_INDEX.md`
4. no missing completion-check referenced files

## Operational Rule

Run this checker before handoff-related commits and before opening a new Codex session for continuation.
