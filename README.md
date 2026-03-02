# Automated Data Extraction & Quality Validation Pipeline
<img width="2788" height="3479" alt="sk_hynix_esg_quality_dashboard" src="https://github.com/user-attachments/assets/1b7155dc-61f0-4a56-9657-538830bd7a89" />

An end-to-end pipeline that automatically extracts, validates, and assesses
structured ESG (Environmental, Social, Governance) metrics from Korean
sustainability reports (PDF).

> **Note:** I acknowledge that this project was pair-programmed with **Claude**
> as an AI coding partner.

---

## Overview

```
Korean PDF reports (e.g.지속가능경영보고서) → Parse → LLM Extract → Validate → Quality Score → Dashboard
```

---

## ESG Metrics

| Category | ID | Metric (KR) | Metric (EN) | Unit | GRI |
|----------|------|-------------------------------|--------------------------------------|---------|----------|
| 🌱 E | E01 | 온실가스 배출량 (Scope 1) | GHG Emissions Scope 1 | tCO2eq | 305-1 |
| 🌱 E | E02 | 온실가스 배출량 (Scope 2) | GHG Emissions Scope 2 | tCO2eq | 305-2 |
| 🌱 E | E03 | 온실가스 배출량 (Scope 3) | GHG Emissions Scope 3 | tCO2eq | 305-3 |
| 🌱 E | E04 | 총 에너지 사용량 | Total Energy Consumption | TJ | 302-1 |
| 🌱 E | E05 | 용수 취수량 | Water Withdrawal | 톤 | 303-3 |
| 🌱 E | E06 | 폐기물 발생량 | Waste Generated | 톤 | 306-3 |
| 🌱 E | E07 | 폐기물 재활용률 | Waste Recycling Rate | % | 306-4 |
| 👥 S | S01 | 총 임직원 수 | Total Employees | 명 | 2-7 |
| 👥 S | S02 | 여성 임직원 비율 | Female Employee Ratio | % | 405-1 |
| 👥 S | S03 | 산업재해율 | Lost Time Injury Rate | % | 403-9 |
| 👥 S | S04 | 1인당 교육훈련 시간 | Training Hours per Employee | 시간 | 404-1 |
| 👥 S | S05 | 이직률 | Employee Turnover Rate | % | 401-1 |
| 🏛 G | G01 | 사외이사 비율 | Independent Director Ratio | % | 2-9 |
| 🏛 G | G02 | 이사회 개최 횟수 | Board Meetings Held | 회 | 2-9 |
| 🏛 G | G03 | 여성 이사 비율 | Female Board Member Ratio | % | 405-1 |
| 🏛 G | G04 | 반부패 교육 이수율 | Anti-corruption Training Rate | % | 205-2 |



## Environment & Performance

| Item | Detail |
|------|--------|
| **OS** | `Ubuntu 22.04 (from WSL 2.6.3.0 on Windows 11) ` |
| **CPU** | `AMD Ryzen 7 57003D` |
| **RAM** | `16GB` |
| **GPU** | 1 $\times$ `NVIDIA GeForce RTX 4080 SUPER (16GB VRAM)` |
| **Python** | `3.11.14` |
| **LLM Backend** | `Ollama + qwen2.5 7B` |

### Processing Time

- Takes around 10 minutes with GPU to process 80-page report.
- Processing time may vary according to your environments, number of pages to process, whether to use GPU, etc..

---

## Installation

### 1. Clone & install dependencies

```bash
git clone https://github.com/binary-cow/esg-example.git
cd esg-example
pip install -r requirements.txt
```


### 2. Set up an LLM backend
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh    # Linux / macOS

# Pull a model
ollama pull qwen2.5:14b       # if you have 24GB+ RAM 
# or, for lighter setups:
ollama pull qwen2.5:7b         # 16GB RAM

# Start the server (if not auto-started)
ollama serve
```
---

## Usage

### Run the full pipeline on a PDF

```bash
# With Ollama (default)
python pipeline.py --pdf ./example/skhynix/report.pdf --backend ollama --model qwen2.5:14b --company sk_hynix --output ./example/skhynix
```

### Run in demo mode (no PDF needed)

```bash
python pipeline.py --demo
```

This generates synthetic ESG data to demonstrate the validation,
quality scoring, and dashboard stages without requiring a real PDF
or LLM backend.

### Full CLI options

```
usage: pipeline.py [-h] [--pdf PDF] [--backend {ollama,groq,openai}]
                   [--model MODEL] [--company COMPANY]
                   [--output OUTPUT] [--demo]

arguments:
  --pdf        Path to ESG report PDF file
  --backend    LLM backend (default: ollama)
  --model      Model name override (default depends on backend)
  --company    Company name for dashboard title
  --output_dir Output path for dashboard image and CSV file 
  --demo       Run with synthetic demo data
```

---

## Pipeline Output

The pipeline produces:

**1. Extracted metrics** — JSON list of structured ESG values with source
references and page numbers.

**2. Validation results** — Each value flagged as `PASS`, `WARNING`, or
`FAIL` based on physical-constraint and business-rule checks
(e.g., percentages must be `[0, 100]`, emissions cannot be negative).

**3. Dashboard PNG** — A single-image report with four panels: quality
score gauges, metric coverage heatmap, validation result distribution,
and per-metric detail table.

---

## To-Do / Roadmap

- ✓ **Revise confidence scoring**

- [ ] **Implement OCR-based PDF parser**: in case of scanned images or have image-embedded tables that `pdfplumber` cannot parse.

- [ ] **Add multiprocessing for faster PDF parsing**

- [ ] **Support additional ESG standards**:
      SASB, TCFD, ISSB (IFRS S1/S2), and CSRD/ESRS metrics.

- [ ] **Implement HuggingFace Transformers backend**

- [ ] **Integrate larger / more capable LLMs**: Test with
      `Qwen2.5-72B-Instruct` (via cloud API) or `Llama 3.1 70B`
      for improved extraction accuracy on complex tables and
      ambiguous contexts.

- [ ] **Add unit and integration tests**: Write `pytest` tests for each
      pipeline stage

- [ ] **Multi-year / multi-company comparison**: Support processing
      multiple reports and generating comparative dashboards showing
      trends over time or cross-company benchmarks.

- [ ] **Build a web interface**: Create a lightweight Streamlit or
      Gradio app for drag-and-drop PDF upload
