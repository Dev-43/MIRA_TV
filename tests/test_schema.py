import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_schema_files_are_valid_json():
    for name in ("focus_event.schema.json", "report.schema.json"):
        json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))


def test_contract_templates_are_valid_json():
    for name in ("scenario.json", "expected_elements.json", "bug_map.json"):
        json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))
