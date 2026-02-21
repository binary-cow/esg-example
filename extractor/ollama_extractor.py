from esg_standards import ESG_METRICS
import json
from typing import List, Dict
import requests


class ESGExtractorOllama:
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

    def _build_prompt(self, text: str, page_num: int) -> str:
        """
        Prompt design for ESG extraction
        In Korean to match the report language, with clear instructions and format.
        """
        metrics_list = "\n".join(
            f"  - {m['id']}: {m['name_kr']} ({m['name_en']}) | "
            f"Unit: {m['unit']} | GRI: {m['gri']}"
            for m in ESG_METRICS
        )
        return f"""당신은 한국 기업 ESG 공시 보고서 데이터 추출 전문가입니다.

아래는 지속가능경영보고서 {page_num}페이지 텍스트입니다.
다음 지표의 값을 찾아 JSON으로 반환하세요.

[대상 지표]
{metrics_list}

[규칙]
1. 해당 지표가 텍스트에 없으면 건너뛰세요.
2. 숫자의 쉼표를 제거하고 순수 숫자만 반환하세요.
3. 반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

[형식]
{{"extracted": [
  {{"metric_id": "E01", "value": 12345.6, "unit": "tCO2eq",
    "year": 2023, "confidence": 0.95,
    "source_text": "원문에서 발췌한 근거 문장"}}
]}}

어떤 지표도 없으면 {{"extracted": []}}

[텍스트]
{text[:3000]}"""

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with the prompt and return raw text response"""
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 2048,
                }
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"]

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
        all_items = []
        total = len(pages)

        for i, page in enumerate(pages):
            print(f"    Processing page {page['page_num']} "
                  f"({i+1}/{total})…", end="", flush=True)
            try:
                prompt = self._build_prompt(
                    page["combined"], page["page_num"]
                )
                raw = self._call_ollama(prompt)
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