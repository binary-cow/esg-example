try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from esg_standards import ESG_METRICS
import json
from typing import List, Dict



class ESGExtractor:
    """
    OpenAI-based extractor for ESG data from Korean reports.
    Uses GPT-4o for better Korean understanding and structured output.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        if not OPENAI_AVAILABLE:
            raise ImportError("pip install openai 필요")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _build_prompt(self, text: str, page_num: int) -> str:
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
3. 반드시 아래 JSON 형식으로만 응답하세요.

[형식]
{{"extracted": [
  {{"metric_id": "E01", "value": 12345.6, "unit": "tCO2eq",
    "year": 2023, "confidence": 0.95,
    "source_text": "원문에서 발췌한 근거 문장"}}
]}}

어떤 지표도 없으면 {{"extracted": []}}

[텍스트]
{text[:4000]}"""

    def extract(self, pages: List[Dict]) -> List[Dict]:
        all_items = []
        for page in pages:
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system",
                         "content": "ESG data extraction specialist. Respond with valid JSON only."},
                        {"role": "user",
                         "content": self._build_prompt(page["combined"], page["page_num"])}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                result = json.loads(resp.choices[0].message.content)
                for item in result.get("extracted", []):
                    item["page_num"] = page["page_num"]
                    all_items.append(item)
            except Exception as e:
                print(f"    ⚠ Page {page['page_num']}: {e}")
        print(f"  ✓ Extracted {len(all_items)} metric values")
        return all_items
    