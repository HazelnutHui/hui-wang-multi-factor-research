# GitHub Publishing Guide (V4)

Last updated: 2026-02-13

This document records how this project is published and maintained on GitHub, including scope control, authentication, commit workflow, and resume usage.

## 1) Repository Identity
- GitHub owner: `HazelnutHui`
- Repository name: `hui-wang-multi-factor-research`
- Default branch: `main`
- Remote URL (HTTPS):
  - `https://github.com/HazelnutHui/hui-wang-multi-factor-research.git`

## 2) Public Positioning
This repository is the **public engineering/research showcase** version of the V4 project.

Primary public value:
- Modular multi-factor backtest system design
- Bias controls (PIT + delisting-aware handling)
- Standardized validation workflow (segmented IC / train-test / walk-forward)
- Reproducible research process and reporting

## 3) What Should Be Public
The public repository should include:
- Core engine code (`backtest/`)
- Strategy code (`strategies/`)
- Research scripts (`scripts/`)
- Configs (`configs/`)
- Tests (`tests/`)
- Public documentation (`README.md`, `RUNBOOK.md`, `STATUS.md`, `PROJECT_SUMMARY.md`, etc.)

## 4) What Must Stay Private / Excluded
The following are intentionally excluded via `.gitignore`:
- `data/`
- `logs/`
- `results/`
- `segment_results/`
- `segment_results_stage0/`
- `walk_forward_results/`
- `archive/`
- strategy output folders (`strategies/*/results`, `runs`, `reports`)
- local notes and secret-bearing artifacts

Reason:
- Prevent secret leakage
- Avoid oversized repository
- Keep public repo focused on engineering/research methodology

## 5) Authentication Standard (HTTPS + PAT)
GitHub no longer supports account-password authentication for Git operations.
Use:
- Username: your GitHub username (`HazelnutHui`)
- Password field: Personal Access Token (PAT)

Recommended PAT setup (fine-grained):
1. Resource owner: `HazelnutHui`
2. Repository access: only `hui-wang-multi-factor-research`
3. Permission: `Contents = Read and write`
4. Expiration: 90 days

Security rules:
- Never paste token in docs, logs, screenshots, or chat history
- If token is exposed, revoke immediately and create a new one

## 6) Local Git Workflow (Standard)
From project root (`/Users/hui/quant_score/v4`):

```bash
git status
git add -A
git commit -m "<clear commit message>"
git push
```

Useful checks before push:

```bash
git status --short
git diff --name-only --cached
```

## 7) One-Time Remote Setup (Already Done)
If needed in a fresh local clone:

```bash
git remote add origin https://github.com/HazelnutHui/hui-wang-multi-factor-research.git
git branch -M main
git push -u origin main
```

## 8) Credential Reset (If Auth Is Wrong)
On macOS, clear stored credential for GitHub:

```bash
printf "protocol=https\nhost=github.com\n" | git credential-osxkeychain erase
```

Then push again and enter correct username + new PAT.

## 9) GitHub Profile / Repo Presentation
Recommended repository About description:

`Bias-aware, reproducible daily-frequency multi-factor alpha research platform with PIT controls, segmented IC validation, and institutional robustness workflow.`

Recommended topics:
- `quant`
- `backtesting`
- `factor-investing`
- `systematic-trading`
- `alpha-research`
- `python`

## 10) Resume Linking Strategy
For resume/interview, prioritize this link:
- One-page summary:
  - `https://github.com/HazelnutHui/hui-wang-multi-factor-research/blob/main/PROJECT_SUMMARY.md`

Optional second link:
- Repo root:
  - `https://github.com/HazelnutHui/hui-wang-multi-factor-research`

## 11) Recommended Commit Message Style
Use concise, scoped messages:
- `docs: update public README and project summary`
- `feat: add stage-2 signal neutralization switch`
- `fix: use forward returns for cross-sectional IC`
- `chore: tighten gitignore for generated artifacts`

## 12) Final Pre-Push Checklist
Before each push, verify:
1. No secrets (API keys/tokens/passwords)
2. No local datasets/logs/results accidentally staged
3. README/project summary still reflect latest status
4. Commit message clearly explains what changed

If all checks pass, push to `main`.
