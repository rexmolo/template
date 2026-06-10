from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "services" / "api"
OUTPUT_PATH = ROOT / "packages" / "contract" / "openapi.json"

sys.path.insert(0, str(API_DIR))

from app.main import create_app  # noqa: E402


def main() -> None:
    spec = create_app().openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
