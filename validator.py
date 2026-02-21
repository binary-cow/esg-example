from esg_standards import ESG_METRICS
import pandas as pd
from typing import List, Dict, Optional

from extractor.base import ESGExtractorBase
class Validator:
    """
    Validate extracted ESG data against business rules.
    Updated: includes confidence-based validation using
    programmatically computed scores.
    Todo: revice confidence calculation to be more robust and interpretable.
    """

    def validate(self, items: List[Dict]) -> List[Dict]:
        validated = []
        for item in items:
            issues = []

            # --- Existing rules (unchanged) ---

            # Rule: value must be numeric
            try:
                val = float(item.get("value", ""))
            except (ValueError, TypeError):
                issues.append({
                    "type": "invalid_value",
                    "severity": "error",
                    "message": f"Non-numeric value: {item.get('value')}",
                })
                val = None

            # Rule: value must be non-negative for most metrics
            if val is not None and val < 0:
                cat = item.get("metric_id", "X")[0]
                if cat in ("E", "S"):
                    issues.append({
                        "type": "negative_value",
                        "severity": "warning",
                        "message": f"Unexpected negative value: {val}",
                    })

            # Rule: year must be plausible
            year = item.get("year", 0)
            # if year is None
            if (not isinstance(year, int) or (not (2018 <= year <= 2026))):
                issues.append({
                    "type": "implausible_year",
                    "severity": "warning",
                    "message": f"Year {year} outside expected range 2018-2026",
                })

            # Rule: metric_id must be recognized
            valid_ids = {m["id"] for m in ESG_METRICS}
            if item.get("metric_id") not in valid_ids:
                issues.append({
                    "type": "unknown_metric",
                    "severity": "error",
                    "message": f"Unrecognized metric_id: "
                               f"{item.get('metric_id')}",
                })

            # --- NEW: confidence-based rules ---

            confidence = item.get("confidence", 0)

            # Flag very low confidence extractions
            if confidence < 0.3:
                issues.append({
                    "type": "low_confidence",
                    "severity": "warning",
                    "message": (
                        f"Extraction confidence is very low "
                        f"({confidence:.2f}). "
                        f"The value may not be reliably extracted."
                    ),
                })

            # Flag when value is not found in source_text
            if not ESGExtractorBase._number_in_text(
                item.get("value"), item.get("source_text", "")
            ):
                issues.append({
                    "type": "value_not_in_source",
                    "severity": "warning",
                    "message": (
                        "Extracted value does not appear in "
                        "the quoted source_text. "
                        "The LLM may have hallucinated."
                    ),
                })

            item["validation_issues"] = issues
            item["is_valid"] = not any(
                i["severity"] == "error" for i in issues
            )
            validated.append(item)

        # Summary
        n_valid = sum(1 for v in validated if v["is_valid"])
        n_warnings = sum(
            1 for v in validated
            if v["validation_issues"]
            and all(i["severity"] == "warning"
                    for i in v["validation_issues"])
        )
        print(f"  ✓ Validation: {n_valid} valid, "
              f"{n_warnings} with warnings, "
              f"{len(validated) - n_valid} errors "
              f"(out of {len(validated)})")

        return validated