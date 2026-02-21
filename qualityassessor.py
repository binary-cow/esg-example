import pandas as pd

from esg_standards import ESG_METRICS
from typing import List, Dict, Optional

class QualityAssessor:
    """
    Assesses quality of extracted ESG data based on multiple dimensions:
    Completeness, Accuracy, Validity, Confidence, Traceability
    """

    def assess(self, df: pd.DataFrame) -> Dict[str, float]:
        if df.empty:
            return {k: 0.0 for k in
                    ["completeness","accuracy","validity","confidence","traceability"]}

        target_ids = {m["id"] for m in ESG_METRICS}
        found_ids = set(df["metric_id"].unique())

        scores = {
            "completeness": len(found_ids & target_ids) / len(target_ids),
            "accuracy": df["chk_in_range"].mean(),
            "validity": df["validation_score"].mean(),
            "confidence": df["confidence"].mean(),
            "traceability": df["chk_has_source"].mean(),
        }
        print("  ✓ Quality Scores:")
        for k, v in scores.items():
            bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
            print(f"    {k:15s} {bar} {v:.0%}")
        return scores