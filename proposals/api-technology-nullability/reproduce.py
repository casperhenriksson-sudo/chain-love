"""Reproduce the documented-blank APIs.technology contract; no network or data edits."""

import copy
import csv
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

from jsonschema.validators import validator_for

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCHEMA_PATH = ROOT / "tools" / "schema.json"
CONVERTER_PATH = ROOT / "tools" / "csv_to_json.py"


def load_converter():
    spec = importlib.util.spec_from_file_location("chainlove_csv_converter", CONVERTER_PATH)
    converter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter)
    return converter


def csv_roundtrip(row, technology, converter):
    """Use the actual CSV loader and normalizer, with only one deliberately blank cell."""
    with tempfile.TemporaryDirectory(prefix=".repro-", dir=HERE) as temporary:
        directory = Path(temporary).resolve()
        assert directory.parent == HERE
        path = directory / "apis.csv"
        raw = {}
        for key, value in row.items():
            if value is None:
                raw[key] = ""
            elif isinstance(value, bool):
                raw[key] = str(value).upper()
            elif isinstance(value, (list, dict)):
                raw[key] = json.dumps(value, ensure_ascii=False)
            else:
                raw[key] = value
        raw["technology"] = technology
        with path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(raw))
            writer.writeheader()
            writer.writerow(raw)
        loaded = converter.load_csv_to_dict_list(str(path))
        normalized, errors = converter.normalize({"apis": loaded})
        assert not errors, errors
        return normalized["apis"][0]


def validate_case(validator, row):
    errors = list(validator.iter_errors({"apis": [row]}))
    return {
        "valid": not errors,
        "errors": [
            {"path": "/" + "/".join(str(part) for part in error.absolute_path),
             "keyword": error.validator, "message": error.message}
            for error in errors
        ],
    }


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    original_type = schema["$defs"]["apis"]["properties"]["technology"]["type"]
    assert original_type == "string", original_type
    assert "technology" in schema["$defs"]["apis"]["required"]
    proposed = copy.deepcopy(schema)
    proposed["$defs"]["apis"]["properties"]["technology"]["type"] = ["string", "null"]
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    validator_class.check_schema(proposed)
    original_validator = validator_class(schema)
    proposed_validator = validator_class(proposed)
    fixture = json.loads((HERE / "valid-api-row.json").read_text(encoding="utf-8"))
    converter = load_converter()
    cases = [("valid_existing_string", fixture, True, True)]
    for name, value in [("empty_csv_cell", ""), ("null_csv_cell", "NULL"),
                        ("whitespace_csv_cell", " ")]:
        normalized = csv_roundtrip(fixture, value, converter)
        assert normalized["technology"] is None
        assert {k: v for k, v in normalized.items() if k != "technology"} == {
            k: v for k, v in fixture.items() if k != "technology"
        }
        cases.append((name, normalized, False, True))
    for name, value in [("integer", 7), ("boolean", False), ("array", []), ("object", {})]:
        modified = {**fixture, "technology": value}
        cases.append((name, modified, False, False))
    missing = {k: v for k, v in fixture.items() if k != "technology"}
    cases.append(("missing_required_key", missing, False, False))
    cases.append(("direct_json_empty_string", {**fixture, "technology": ""}, True, True))

    results = []
    for name, row, original_expected, proposed_expected in cases:
        original_result = validate_case(original_validator, row)
        proposed_result = validate_case(proposed_validator, row)
        assert original_result["valid"] is original_expected, (name, original_result)
        assert proposed_result["valid"] is proposed_expected, (name, proposed_result)
        results.append({"case": name, "current": original_result, "proposed": proposed_result})

    report = {
        "source_tools_revision": "830d5f05ae15954c43ef23f4085c83d4548d5431",
        "fixture_data_revision": "a5a4277ea76394eef5e721bccae3dbab376e887c",
        "fixture_slug": fixture["slug"],
        "fixture_note": "PublicNode's actual technology is known; blank values are synthetic inputs only.",
        "validator": validator_class.__name__,
        "schema_sha256_as_read": hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest(),
        "schema_pointer": "/$defs/apis/properties/technology/type",
        "proposed_type_only": ["string", "null"],
        "required_key_retained": True,
        "case_count": len(results),
        "validation_count": 2 * len(results),
        "all_expected_outcomes_observed": True,
        "production_schema_modified": False,
        "network_calls": 0,
        "cases": results,
    }
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["case_count", "validation_count",
          "all_expected_outcomes_observed", "required_key_retained", "production_schema_modified"]}))


if __name__ == "__main__":
    main()
