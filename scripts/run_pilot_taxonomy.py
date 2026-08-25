#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.pilot_taxonomy import build
print(json.dumps(build(ROOT),indent=2,sort_keys=True))
