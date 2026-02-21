from esg_standards import ESG_METRICS
import pandas as pd
from typing import List, Dict, Optional

class Validator:
    """
    validate with business rules and ESG standards
    numeric, range, unit, year, source
    """

    def __init__(self):
        self.defs = {m["id"]: m for m in ESG_METRICS}

    def validate(self, extracted: List[Dict]) -> pd.DataFrame:
        rows = []
        for item in extracted:
            mid = item.get("metric_id", "")
            d = self.defs.get(mid, {})
            val = item.get("value")

            checks = {
                "is_numeric": isinstance(val, (int, float)) and val is not None,
                "in_range": False,
                "unit_match": item.get("unit", "").strip() == d.get("unit", ""),
                "has_year": isinstance(item.get("year"), int)
                            and 2000 <= item.get("year", 0) <= 2026,
                "has_source": bool(item.get("source_text", "").strip()),
            }
            if checks["is_numeric"] and d.get("valid_range"):
                lo, hi = d["valid_range"]
                checks["in_range"] = lo <= float(val) <= hi

            passed = sum(checks.values())
            total = len(checks)

            rows.append({
                "metric_id": mid,
                "category": d.get("category", ""),
                "name_en": d.get("name_en", ""),
                "name_kr": d.get("name_kr", ""),
                "gri": d.get("gri", ""),
                "value": val,
                "unit": item.get("unit", ""),
                "year": item.get("year"),
                "page_num": item.get("page_num"),
                "confidence": item.get("confidence", 0),
                "source_text": item.get("source_text", ""),
                "validation_score": passed / total,
                "checks_passed": passed,
                "checks_total": total,
                **{f"chk_{k}": v for k, v in checks.items()},
            })

        df = pd.DataFrame(rows)
        if len(df):
            print(f"  ✓ Validated {len(df)} items — "
                  f"avg score {df['validation_score'].mean():.0%}")
        return df