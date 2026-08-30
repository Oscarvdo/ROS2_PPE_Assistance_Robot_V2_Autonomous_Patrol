import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for package in ("ppe_perception", "ppe_decision", "ppe_alert", "ppe_logger", "ppe_navigation"):
    sys.path.insert(0, str(ROOT / package))
