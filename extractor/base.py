from abc import ABC, abstractmethod
from esg_standards import ESG_METRICS
import json
from typing import List, Dict, Optional


class ESGExtractorBase(ABC):
    """Base class for all ESG extraction backends."""

    # --- Shared methods (all backends use these as-is) ---

    def _build_prompt(self, text: str, page_num: int) -> str:
        """
        Build extraction prompt with placeholder-based schema
        to prevent value anchoring.

        Key changes from v1:
        - No confidence field (computed post-hoc)
        - Schema uses <placeholder> notation instead of concrete values
        - Explicit "do not guess" instruction
        - Verbatim source_text instruction to improve traceability
        """
        metrics_list = "\n".join(
            f"  - {m['id']}: {m['name_kr']} ({m['name_en']}) "
            f"[Unit: {m['unit']}] [GRI: {m['gri']}]"
            for m in ESG_METRICS
        )

        return f"""You are a specialist in extracting structured ESG data from Korean corporate sustainability reports.

    Below is text from page {page_num} of a Korean sustainability report.
    Identify numeric values for the ESG metrics listed below and return them as JSON.

    [Target Metrics]
    {metrics_list}

    [Instructions]
    1. ONLY extract metrics whose numeric values are explicitly stated in the text.
    2. Do NOT guess, estimate, or infer any values. If a metric is absent, skip it entirely.
    3. Strip commas from numbers before returning (e.g. "1,234.5" becomes 1234.5).
    4. If the same metric appears for multiple years, create one entry per year.
    5. For "source_text", copy the EXACT sentence or table row verbatim. Do NOT paraphrase.
    6. Return ONLY the JSON object described below. No explanations, no markdown fences, no extra text.

    [Output Schema]
    {{
    "extracted": [
        {{
        "metric_id": "<ID from the metrics list>",
        "value": <numeric value>,
        "unit": "<unit of measurement>",
        "year": <four-digit year>,
        "source_text": "<verbatim quote from the text>"
        }}
    ]
    }}

    Return {{"extracted": []}} if none of the target metrics are found.

    [Page {page_num} Text]
    {text[:3000]}"""



    def _compute_confidence(self, item: dict, page_text: str) -> float:
        """
        Compute extraction confidence from verifiable signals
        instead of relying on LLM self-assessment.

        Scoring rubric (max 1.0):
        +0.30  value is found in the original page text
        +0.25  value is found in the quoted source_text
        +0.20  unit matches the expected unit for this metric
        +0.10  year is within plausible range (2018-2026)
        +0.15  source_text is substantial (>= 15 chars)
        """
        score = 0.0
        value = item.get("value")
        source = item.get("source_text", "")
        metric_id = item.get("metric_id", "")
        year = item.get("year", 0)
        unit = item.get("unit", "")

        # Signal 1: value appears in the original page text
        if self._number_in_text(value, page_text):
            score += 0.30

        # Signal 2: value appears in the quoted source_text
        if self._number_in_text(value, source):
            score += 0.25

        # Signal 3: unit matches expected unit for this metric
        expected_unit = self._get_expected_unit(metric_id)
        if expected_unit and unit:
            if unit.strip().lower() == expected_unit.strip().lower():
                score += 0.20
            elif (expected_unit.lower() in unit.lower()
                or unit.lower() in expected_unit.lower()):
                # Partial match, e.g. "tCO2eq" vs "tCO2eq/year"
                score += 0.10

        # Signal 4: year is plausible
        if isinstance(year, (int, float)) and 2018 <= int(year) <= 2026:
            score += 0.10

        # Signal 5: source_text is substantial
        if source and len(source.strip()) >= 15:
            score += 0.15
        elif source and len(source.strip()) >= 5:
            score += 0.07

        return round(min(score, 1.0), 2)


    @staticmethod
    def _number_in_text(value, text: str) -> bool:
        """
        Check whether a numeric value appears in text,
        accounting for comma-formatted numbers.
        e.g. value=12345.6 matches "12,345.6" or "12345.6" in text.
        """
        if value is None or not text:
            return False
        try:
            val_f = float(value)
        except (ValueError, TypeError):
            return False

        # Exact string match
        if str(value) in text:
            return True

        # Integer form match
        try:
            int_val = int(val_f)
            if str(int_val) in text:
                return True
            # Comma-formatted integer (Korean/English style)
            if f"{int_val:,}" in text:
                return True
        except (ValueError, OverflowError):
            pass

        # Float with common formatting
        if f"{val_f:,.1f}" in text or f"{val_f:.1f}" in text:
            return True

        return False


    def _get_expected_unit(self, metric_id: str) -> str:
        """Look up the expected unit for a given metric ID."""
        for m in ESG_METRICS:
            if m["id"] == metric_id:
                return m["unit"]
        return ""

    def _parse_json(self, text: str) -> Dict:
        """
        Extract JSON object from the model's response text
        Robust parsing to handle potential formatting issues from the LLM output.
        """

        # 1: Parse entire text as JSON (if model followed instructions perfectly)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2: Extract JSON from code block (if model wrapped it in ```json ... ```)
        import re
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 3: Extract first JSON-like substring (fallback)
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {"extracted": []}

    def extract(self, pages: List[Dict]) -> List[Dict]:
        """
        Run extraction on all pages.
        Confidence is computed programmatically after LLM extraction.
        """
        all_items = []
        total = len(pages)

        for i, page in enumerate(pages):
            print(
                f"    Processing page {page['page_num']} "
                f"({i + 1}/{total})…",
                end="", flush=True,
            )
            try:
                prompt = self._build_prompt(
                    page["combined"], page["page_num"]
                )
                raw = self._call_llm(prompt)
                result = self._parse_json(raw)

                items = result.get("extracted", [])
                for item in items:
                    item["page_num"] = page["page_num"]

                    # Remove any LLM-generated confidence
                    # (in case the model adds it despite not being asked)
                    item.pop("confidence", None)

                    # Compute confidence from verifiable signals
                    item["confidence"] = self._compute_confidence(
                        item, page["combined"]
                    )
                    all_items.append(item)

                print(f" → {len(items)} metrics found")

            except Exception as e:
                print(f" ⚠ Error: {e}")

        print(f"  ✓ Extracted {len(all_items)} metric values total")
        return all_items

    # --- Must be implemented by each subclass ---

    @abstractmethod
    def _call_llm(self, prompt: str) -> str:
        """Send prompt to LLM and return raw text response."""
        ...
