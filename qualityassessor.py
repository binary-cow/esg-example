import pandas as pd

from esg_standards import ESG_METRICS
from typing import List, Dict, Optional

class QualityAssessor:
    """
    Assesses quality of extracted ESG data based on five dimensions:
    Completeness, Accuracy, Validity, Confidence, Traceability.

    Takes validated items (output of Validator.validate()) directly.
    All quality signals are computed internally — no pre-computed columns required.
    """

    # Plausible value ranges per metric category prefix
    # Used for accuracy scoring (sanity check, not ground truth)
    RANGE_BOUNDS = {
        "E01": (0, 1e9),         # GHG Scope1: 0 ~ 1B tCO2eq
        "E02": (0, 1e9),         # GHG Scope2
        "E03": (0, 1e9),         # GHG Scope3
        "E04": (0, 1e12),        # Energy usage: 0 ~ 1T TJ
        "E05": (0, 100),         # Renewable energy ratio: 0 ~ 100%
        "E06": (0, 1e12),        # Water usage
        "E07": (0, 1e12),        # Waste generated
        "E08": (0, 100),         # Waste recycling rate: 0 ~ 100%
        "S01": (0, 1e7),         # Total employees
        "S02": (0, 100),         # Female employee ratio: 0 ~ 100%
        "S03": (0, 100),         # Female leadership ratio
        "S04": (0, 100),         # Turnover rate
        "S05": (0, 1e6),         # Training hours per person
        "S06": (0, 100),         # Industrial accident rate
        "G01": (0, 100),         # Board independence ratio
        "G02": (0, 100),         # Female board ratio
        "G03": (0, 50),          # Board meetings per year
        "G04": (0, 100),         # Attendance rate
        "G05": (0, 1e12),        # Ethics violations / anti-corruption fines
    }

    def assess(self, validated_items: List[Dict]) -> Dict[str, float]:
        """
        Compute quality scores from validated extraction results.

        Args:
            validated_items: output of Validator.validate().
                Each item has: metric_id, value, unit, year,
                source_text, page_num, confidence,
                validation_issues, is_valid

        Returns:
            Dict with five quality dimension scores (0.0 ~ 1.0)
        """
        if not validated_items:
            return {k: 0.0 for k in [
                "completeness", "accuracy", "validity",
                "confidence", "traceability",
            ]}

        target_ids = {m["id"] for m in ESG_METRICS}
        found_ids = {item["metric_id"] for item in validated_items
                     if item.get("metric_id")}

        # --- Completeness: fraction of target metrics found ---
        completeness = (
            len(found_ids & target_ids) / len(target_ids)
            if target_ids else 0.0
        )

        # --- Accuracy: fraction of values within plausible ranges ---
        range_checks = []
        for item in validated_items:
            in_range = self._check_in_range(
                item.get("metric_id"), item.get("value")
            )
            range_checks.append(in_range)

        accuracy = (
            sum(range_checks) / len(range_checks)
            if range_checks else 0.0
        )

        # --- Validity: fraction of items with no error-level issues ---
        validity_scores = []
        for item in validated_items:
            issues = item.get("validation_issues", [])
            error_count = sum(
                1 for i in issues if i.get("severity") == "error"
            )
            warning_count = sum(
                1 for i in issues if i.get("severity") == "warning"
            )
            if error_count > 0:
                validity_scores.append(0.0)
            elif warning_count > 0:
                # Deduct 0.2 per warning, floor at 0.3
                validity_scores.append(max(0.3, 1.0 - 0.2 * warning_count))
            else:
                validity_scores.append(1.0)

        validity = (
            sum(validity_scores) / len(validity_scores)
            if validity_scores else 0.0
        )

        # --- Confidence: mean of programmatically computed confidence ---
        confidences = [
            item.get("confidence", 0.0) for item in validated_items
        ]
        confidence = (
            sum(confidences) / len(confidences)
            if confidences else 0.0
        )

        # --- Traceability: fraction of items with substantial source_text ---
        trace_checks = []
        for item in validated_items:
            source = item.get("source_text", "")
            has_source = isinstance(source, str) and len(source.strip()) >= 10
            trace_checks.append(1.0 if has_source else 0.0)

        traceability = (
            sum(trace_checks) / len(trace_checks)
            if trace_checks else 0.0
        )

        scores = {
            "completeness": round(completeness, 4),
            "accuracy": round(accuracy, 4),
            "validity": round(validity, 4),
            "confidence": round(confidence, 4),
            "traceability": round(traceability, 4),
        }

        self._print_scores(scores)
        return scores

    def _check_in_range(self, metric_id: str, value) -> bool:
        """
        Check whether a value falls within the plausible range
        for the given metric. Returns True if no bounds are defined.
        """
        if value is None:
            return False
        try:
            val = float(value)
        except (ValueError, TypeError):
            return False

        bounds = self.RANGE_BOUNDS.get(metric_id)
        if bounds is None:
            # No bounds defined — assume OK
            return True

        lo, hi = bounds
        return lo <= val <= hi

    @staticmethod
    def _print_scores(scores: Dict[str, float]) -> None:
        """Print quality scores with visual bar chart."""
        print("  ✓ Quality Scores:")
        for k, v in scores.items():
            filled = int(v * 20)
            bar = "█" * filled + "░" * (20 - filled)
            print(f"    {k:15s} {bar} {v:.0%}")