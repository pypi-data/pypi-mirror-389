import json
import csv
from typing import List, Dict
from pathlib import Path


def load_json(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: str) -> List[Dict]:
    with open(path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def save_json(path: str, data: Dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_validation_set(path: str) -> List[Dict]:
    """
    Loads a validation dataset (QA pairs) from JSON or CSV.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Validation file not found: {path}")

    if p.suffix.lower() == ".json":
        return load_json(path)
    elif p.suffix.lower() in [".csv", ".tsv"]:
        return load_csv(path)
    else:
        raise ValueError("Unsupported validation set format. Use JSON or CSV.")