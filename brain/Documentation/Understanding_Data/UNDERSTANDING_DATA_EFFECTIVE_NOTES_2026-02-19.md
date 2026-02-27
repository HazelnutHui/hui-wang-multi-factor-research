# Understanding Data (2 Articles) Effective Notes

Source files:
- `brain/results/understanding_data_docs/51.txt`
- `brain/results/understanding_data_docs/52.txt`

Goal:
- Keep only operational rules for field selection, coverage diagnostics, and faster data discovery.

## 1) Core Concepts You Must Get Right
- `Data Field`: one named variable with consistent type + business meaning.
- `Dataset`: collection of related data fields.
- `Matrix field`: one value per `(date, instrument)`; directly usable in most expressions.
- `Vector field`: multiple values per `(date, instrument)`; must be reduced with vector operators before mixing with matrix fields.
  - If not converted, expression errors are expected.

## 2) New Field Quick-Diagnosis Framework (From Docs)
Use neutralization=`None`, decay=`0` for diagnostics.

### Coverage
- Expression:
  - `datafield`
  - or `datafield != 0 ? 1 : 0`
- Insight:
  - Approximate coverage from `(LongCount + ShortCount) / UniverseSize`.
  - Non-zero ratio check helps detect sparse effective coverage.

### Update frequency / staleness behavior
- Expression:
  - `ts_std_dev(datafield, N) != 0 ? 1 : 0`
- Insight:
  - Vary `N` (e.g., 5, 22, 66) to infer whether field changes weekly/monthly/quarterly.

### Range / bounds
- Expression:
  - `abs(datafield) > X`
- Insight:
  - Sweep `X` to understand scale and whether field is likely normalized.

### Central tendency
- Expression:
  - `ts_median(datafield, 1000) > X`
- Insight:
  - Sweep threshold to locate long-run median/mean region.

### Distribution shape
- Expression:
  - `X < scale_down(datafield) && scale_down(datafield) < Y`
- Insight:
  - `scale_down` preserves distribution form while normalizing range; useful for bucket occupancy checks.

## 3) Coverage Handling (Practical)
- Low-coverage fields should usually be paired with:
  - `ts_backfill`
  - `kth_element`
  - `group_backfill`
- Do not assume backfill is always pre-applied; behavior differs by dataset.

## 4) Data Explorer: Fast Workflow
- Pre-set `Region`, `Delay`, `Universe` before searching.
- Search modes:
  - by idea keyword (NLP-style)
  - by strict criteria (coverage/type/alpha-count/user-count)
  - by dataset category/name
- Use crowding signals:
  - sort/filter by alpha count and user count to find less crowded candidates.

## 5) Search Quality Rules (3Ss + synonyms)
- Keep queries:
  - short
  - simple
  - straightforward
- Use both full term and abbreviation:
  - `earnings per share` + `eps`
  - `implied volatility` + `iv`
- If exact term unknown, query natural-language paraphrases first.

## 6) Immediate Application to Your Alpha Build Loop
1. Before coding signal logic, run quick diagnostics on each candidate field.
2. Drop fields with poor effective coverage unless compensated by robust backfill logic.
3. Standardize field-scale understanding (bounds + median + distribution) before blending.
4. Prefer fields with acceptable coverage and lower crowding, then test alpha robustness.

