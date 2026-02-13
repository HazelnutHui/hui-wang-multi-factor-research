import sys
from pathlib import Path

# Ensure project root on sys.path for backtest imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
