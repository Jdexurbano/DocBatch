import sys
from pathlib import Path

_SOURCE_ROOT = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SOURCE_ROOT))
