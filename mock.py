import numpy as np
from typing import List, Dict
from esg_standards import ESG_METRICS

# mock data generator for testing and demo purposes
def generate_mock_data() -> List[Dict]:
    
    np.random.seed(2026)  # for reproducibility
    mock = {
        "E01": (245000,  .95, "Scope 1 온실가스 직접배출량: 245,000 tCO2eq"), # GHG direct emissions
        "E02": (189000,  .93, "Scope 2 온실가스 간접배출량: 189,000 tCO2eq"), # GHG indirect emissions from purchased electricity
        "E03": (1520000, .72, "Scope 3 기타 간접배출량: 약 1,520,000 tCO2eq (추정치)"), # GHG indirect emissions from value chain
        "E04": (4521,    .91, "총 에너지 사용량 4,521 TJ"), # Total energy consumption
        "E05": (32500000,.88, "용수 취수량: 32,500천톤"), # Water withdrawal
        "E06": (78500,   .90, "폐기물 총 발생량 78,500톤"), # Waste generated
        "E07": (92.3,    .94, "폐기물 재활용률 92.3%"), # Waste recycling rate
        "S01": (63500,   .97, "총 임직원 수: 63,500명"), # Total employees
        "S02": (28.5,    .89, "여성 임직원 비율 28.5%"), # Female employee ratio
        "S03": (0.12,    .85, "산업재해율 0.12%"), # Lost time injury rate
        "S04": (62,      .82, "1인당 평균 교육시간: 62시간"), # Training hours per employee
        # S05 이직률 (Employee Turnover Rate) — Omit to test missing data handling
        "G01": (57.1,    .96, "사외이사 비율: 57.1%"), # Independent director ratio
        "G02": (14,      .98, "이사회 개최: 연 14회"), # Board meetings held a year
        # G03 여성이사비율 (Female Board Member Ratio) — Omit to test missing data handling
        "G04": (98.5,    .91, "반부패 교육 이수율 98.5%"), # Anti-corruption training rate
    }
    items = []
    for mid, (val, conf, src) in mock.items():
        d = next(m for m in ESG_METRICS if m["id"] == mid)
        items.append({
            "metric_id": mid, "value": val, "unit": d["unit"],
            "year": 2023, "page_num": np.random.randint(15, 85),
            "confidence": conf, "source_text": src,
        })
    return items