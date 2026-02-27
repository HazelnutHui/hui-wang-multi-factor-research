import csv, pathlib, os, subprocess, sys
api_key=os.environ.get("FMP_API_KEY")
if not api_key:
    sys.exit("FMP_API_KEY not set")
src=pathlib.Path("/Users/hui/quant_score/v4/data/fmp/symbols_us_basic.csv")
out_dir="/Users/hui/quant_score/v4/data/fmp/market_cap_history"
py=os.environ.get("PYTHON_BIN") or "/Users/hui/miniconda3/bin/python3"
script="/Users/hui/quant_score/v4/scripts/fmp_market_cap_history.py"

syms=[]
with src.open(newline='', encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
        s=(row.get("symbol") or "").strip()
        if s:
            syms.append(s)

batch=500
for i in range(0, len(syms), batch):
    j=min(i+batch, len(syms))
    tmp=pathlib.Path(f"/tmp/market_cap_symbols_{i+1:04d}_{j:04d}.csv")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["symbol"])
        w.writeheader()
        for s in syms[i:j]:
            w.writerow({"symbol": s})
    print(f"Batch {i+1}-{j} -> {tmp}")
    log_path = pathlib.Path(f"/tmp/market_cap_batch_{i+1:04d}_{j:04d}.log")
    with log_path.open("w", encoding="utf-8") as log:
        subprocess.call([py, script, "--api-key", api_key, "--symbols-csv", str(tmp), "--out-dir", out_dir],
                        stdout=log, stderr=log)
    print(f"log saved: {log_path}")
    try:
        err_count = 0
        code_counts = {}
        with log_path.open("r", encoding="utf-8") as log:
            for line in log:
                if "Error " in line:
                    err_count += 1
                for code in (" 401 ", " 403 ", " 429 ", " 500 ", " 502 ", " 503 "):
                    if code in line:
                        code_counts[code.strip()] = code_counts.get(code.strip(), 0) + 1
        if err_count or code_counts:
            print(f"errors: {err_count} http={code_counts}")
    except Exception as exc:
        print(f"log summary failed: {exc}")
    input("Press Enter to continue next batch...")
