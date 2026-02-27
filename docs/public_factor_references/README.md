# Public Factor References Folder

Last updated: 2026-02-22

## Files
- `FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_EN.md`
  - Detailed English reference of public factor formulas, execution constraints, and V4 implementation audit.
- `FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_CN.md`
  - 中文版（与英文版结构对齐）

## Usage
- Use EN file for external/public presentation and citation.
- Use CN file for internal planning, review, and implementation alignment.
- Latest online source revalidation checkpoint: `2026-02-22` (Ken French / MSCI / AQR / Qlib).

## Update Rules
- Keep EN/CN structure aligned by section number when possible.
- When adding a new factor, include:
  1. exact formula
  2. signal direction
  3. data/PIT requirements
  4. execution constraints
  5. common failure modes
- Update timestamp when changing methodology or source links.
- Keep a channel note for every major update:
  - academic/official source updates
  - open-source implementation updates
  - V4 internal evidence feedback (`gate_results`, `audit/failure_patterns`)
- For batch experiments, define discrete parameter groups first, then run; avoid ad-hoc continuous tuning.
