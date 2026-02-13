"""Download all Owner Earnings-labeled data once"""
import pandas as pd
import requests
import time
import os
from glob import glob

API_KEY = "xW9GGtIZOfJeA2r2YBvqrLLFNs0oF8ov"
BASE_URL = "https://financialmodelingprep.com/stable"
OWNER_EARNINGS_DIR = "./data/Owner_Earnings"
os.makedirs(OWNER_EARNINGS_DIR, exist_ok=True)

# Get all symbols
active_files = glob("./data/prices/*.pkl")
delisted_files = glob("./data/prices_delisted/*.pkl")

symbols = set()
for f in active_files + delisted_files:
    sym = os.path.basename(f).replace('.pkl', '')
    symbols.add(sym)

symbols = sorted(list(symbols))
print(f"Total symbols: {len(symbols)}")

success = 0
cached = 0
failed = 0

for i, symbol in enumerate(symbols):
    if (i+1) % 100 == 0:
        print(f"[{i+1}/{len(symbols)}] Success:{success} Cached:{cached} Failed:{failed}")
    
    cache_file = f"{OWNER_EARNINGS_DIR}/{symbol}.pkl"
    
    if os.path.exists(cache_file):
        cached += 1
        continue
    
    url = f"{BASE_URL}/earnings"
    params = {'symbol': symbol, 'apikey': API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        time.sleep(0.12)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.to_pickle(cache_file)
                success += 1
            else:
                failed += 1
        else:
            failed += 1
    except:
        failed += 1

print(f"\nComplete: Downloaded:{success} Cached:{cached} Failed:{failed}")
