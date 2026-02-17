# Website Handoff (Hui Quant Dashboard)

Last updated: 2026-02-17

## 1) Scope
- Website project path: `/Users/hui/Hui`
- Current objective:
  - Keep existing visual style
  - Migrate old content to current V4 quant workflow
  - Make non-quant users understand the pipeline quickly
  - Keep technical depth available for advanced users

## 2) What Is Already Done
- Backend:
  - Added `GET /api/quant/research_context` in `app/main.py`
  - Extended `app/data_loader.py` to provide:
    - core strategy summary
    - single-factor Stage1/Stage2 IC snapshot
    - combo config + Stage2 constraints
    - system architecture + workflow steps
  - Added fallback parser from `v4/STATUS.md` so dashboard still shows IC summary when `segment_results` are not fully synced locally.
- Frontend:
  - Added "研究与系统细节" card and detail area in `app/static/index.html`
  - Added:
    - clickable factor drill-down
    - beginner path ("先结论后技术")
    - collapsible timeline ("单因子 -> 组合 -> 三层回测")
  - Added rendering and interactions in `app/static/app.js`
  - Added styles for new modules in `app/static/styles.css`
- Visibility fix:
  - `research-detail` default visible (not hidden)
  - `research-board` prevented from being auto-collapsed by old localStorage state

## 3) Current Live-Check Commands (Local)
```bash
cd /Users/hui/Hui

# confirm latest html/js markers
grep -n "research-factor-detail\\|research-beginner\\|research-timeline" app/static/index.html
grep -n "renderResearchFactorDetail\\|renderResearchBeginner\\|renderResearchTimeline" app/static/app.js

# run local server (venv recommended)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

Access:
- Local: `http://127.0.0.1:8010`
- Tailscale/LAN: `http://100.103.43.29:8010`

## 4) If UI Looks Old
1. Ensure server is started from `/Users/hui/Hui`.
2. Hard refresh browser (`Cmd+Shift+R`).
3. Clear service worker cache:
   - DevTools -> Application -> Service Workers -> Unregister
   - Application -> Clear storage -> Clear site data
4. Reset collapse state:
```js
localStorage.removeItem('collapsedCards'); location.reload();
```

## 5) What Is Real Data vs Placeholder
- Real now:
  - Signal leaderboard
  - Strategy IC trend / backtest summary
  - Research card: factor IC, combo params, Stage2 constraints, architecture/workflow
- Placeholder now:
  - 异常雷达 / 事件链 / 过度反应 / 同业对比 / 叙事窗口
  - These still need real event/news pipelines.

## 6) Known Gaps (Next Priorities)
1. Factor-combo IC matrix page:
   - show pair-level combo IC (factor x factor)
   - requires explicit combo batch outputs as data source
2. Parameter table export:
   - Stage1 / Stage2 / Combo grouped parameter table
   - CSV download button for audit/share
3. Public-vs-technical mode toggle:
   - "Quick View" for non-quant users
   - "Research View" for full parameter and methodology detail
4. Deployment runbook for `whalpha.com`:
   - pull latest code
   - restart service
   - clear CDN/service-worker cache

## 7) Suggested Prompt for New Codex Session
Use these files first:
1. `WEBSITE_HANDOFF.md`
2. `STATUS.md`
3. `PROJECT_SUMMARY.md`
4. `DOCS_INDEX.md`

Then request:
- "Continue dashboard work from WEBSITE_HANDOFF.md; implement factor-combo IC matrix and parameter export without changing global visual style."

