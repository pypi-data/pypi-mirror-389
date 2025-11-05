import sys
from pathlib import Path

# Ensure the src directory is on sys.path so the ariadne package can be imported
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))
