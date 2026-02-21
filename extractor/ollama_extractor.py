from esg_standards import ESG_METRICS
import json
from typing import List, Dict
import requests
from extractor.base import ESGExtractorBase


class ESGExtractorOllama(ESGExtractorBase):
    """Ollama-based extractor for local LLMs — qwen, llama3, etc."""

    def __init__(self, model: str = "qwen2.5:14b",
                 base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

        # Check connection and model availability
        try:
            r = requests.get(f"{base_url}/api/tags", timeout=5)
            models = [m["name"] for m in r.json().get("models", [])]
            if not any(model.split(":")[0] in m for m in models):
                print(f"  ⚠ '{model}' not found. Available: {models}")
                print(f"    Run: ollama pull {model}")
        except requests.ConnectionError:
            raise ConnectionError(
                "Server connection failed. Is Ollama running?"
            )
    
    # def _build_prompt(self, text: str, page_num: int) -> str:
    #     """
    #     Build extraction prompt with placeholder-based schema
    #     to prevent value anchoring.

    #     Key changes from v1:
    #     - No confidence field (computed post-hoc)
    #     - Schema uses <placeholder> notation instead of concrete values
    #     - Explicit "do not guess" instruction
    #     - Verbatim source_text instruction to improve traceability
    #     """
    #     metrics_list = "\n".join(
    #         f"  - {m['id']}: {m['name_kr']} ({m['name_en']}) "
    #         f"[Unit: {m['unit']}] [GRI: {m['gri']}]"
    #         for m in ESG_METRICS
    #     )

    #     return f"""You are a specialist in extracting structured ESG data from Korean corporate sustainability reports.

    # Below is text from page {page_num} of a Korean sustainability report.
    # Identify numeric values for the ESG metrics listed below and return them as JSON.

    # [Target Metrics]
    # {metrics_list}

    # [Instructions]
    # 1. ONLY extract metrics whose numeric values are explicitly stated in the text.
    # 2. Do NOT guess, estimate, or infer any values. If a metric is absent, skip it entirely.
    # 3. Strip commas from numbers before returning (e.g. "1,234.5" becomes 1234.5).
    # 4. If the same metric appears for multiple years, create one entry per year.
    # 5. For "source_text", copy the EXACT sentence or table row verbatim. Do NOT paraphrase.
    # 6. Return ONLY the JSON object described below. No explanations, no markdown fences, no extra text.

    # [Output Schema]
    # {{
    # "extracted": [
    #     {{
    #     "metric_id": "<ID from the metrics list>",
    #     "value": <numeric value>,
    #     "unit": "<unit of measurement>",
    #     "year": <four-digit year>,
    #     "source_text": "<verbatim quote from the text>"
    #     }}
    # ]
    # }}

    # Return {{"extracted": []}} if none of the target metrics are found.

    # [Page {page_num} Text]
    # {text[:3000]}"""

    def _call_llm(self, prompt: str) -> str:
        """Send prompt to Ollama and return raw response text."""
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 2048,
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"]
    # def _call_ollama(self, prompt: str) -> str:
    #     """Call Ollama API with the prompt and return raw text response"""
    #     resp = requests.post(
    #         f"{self.base_url}/api/generate",
    #         json={
    #             "model": self.model,
    #             "prompt": prompt,
    #             "stream": False,
    #             "options": {
    #                 "temperature": 0.0,
    #                 "num_predict": 2048,
    #             }
    #         },
    #         timeout=120,
    #     )
    #     resp.raise_for_status()
    #     return resp.json()["response"]

    # def _parse_json(self, text: str) -> Dict:
    #     """
    #     Extract JSON object from the model's response text
    #     Robust parsing to handle potential formatting issues from the LLM output.
    #     """

    #     # 1: Parse entire text as JSON (if model followed instructions perfectly)
    #     try:
    #         return json.loads(text)
    #     except json.JSONDecodeError:
    #         pass

    #     # 2: Extract JSON from code block (if model wrapped it in ```json ... ```)
    #     import re
    #     match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    #     if match:
    #         try:
    #             return json.loads(match.group(1))
    #         except json.JSONDecodeError:
    #             pass

    #     # 3: Extract first JSON-like substring (fallback)
    #     match = re.search(r'\{.*\}', text, re.DOTALL)
    #     if match:
    #         try:
    #             return json.loads(match.group(0))
    #         except json.JSONDecodeError:
    #             pass

    #     return {"extracted": []}

    def extract(self, pages: List[Dict]) -> List[Dict]:
        all_items = []
        total = len(pages)

        for i, page in enumerate(pages):
            print(f"    Processing page {page['page_num']} "
                  f"({i+1}/{total})…", end="", flush=True)
            try:
                prompt = self._build_prompt(
                    page["combined"], page["page_num"]
                )
                raw = self._call_llm(prompt)
                result = self._parse_json(raw)

                items = result.get("extracted", [])
                for item in items:
                    item["page_num"] = page["page_num"]
                    all_items.append(item)

                print(f" → {len(items)} metrics found")

            except Exception as e:
                print(f" ⚠ Error: {e}")

        print(f"  ✓ Extracted {len(all_items)} metric values total")
        return all_items