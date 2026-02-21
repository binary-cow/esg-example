#!/usr/bin/env python3
"""
Korean ESG Disclosure Data Extraction & Quality Assessment Pipeline
===================================================================
Extracts structured ESG metrics from Korean PDF sustainability reports,
validates data quality, and generates a comprehensive quality dashboard.

Usage:
    python esg_pipeline.py --demo                        # Mock data demo
    python esg_pipeline.py --pdf report.pdf --api_key sk-...  # Real PDF

Requirements:
    pip install pdfplumber openai pandas numpy matplotlib
"""

import argparse
import os

from dashboard import Dashboard
# from extractor.init_extractor import ESGExtractor, ESGExtractorOllama
from parser import PDFParser
from qualityassessor import QualityAssessor
from validator import Validator
from mock import generate_mock_data
from extractor.init_extractor import create_extractor
import pandas as pd

# Main pipeline function
def run_pipeline(pdf_path=None, 
                 api_key=None, 
                 demo=False,
                 company="KOREAN CORPORATION",
                 save_dir="./esg_quality_dashboard"
                 ):

    print("=" * 60)
    print("=" * 60)

    # 1: Parse data from PDF and extract ESG metrics using LLM
    if demo:
        print("\n[1/4] Mock data mode")
        extracted = generate_mock_data()
    else:
        print("\n[1/4] Parsing PDF…")
        pages = PDFParser(pdf_path).parse()
        print("[2/4] LLM extraction…")

        # LLM choice and extractor initialization
        extractor = create_extractor(backend=args.backend)
        extracted = extractor.extract(pages)

    # 2: Validate
    print("\n[2/4] Validating…" if demo else "\n[3/4] Validating…")
    df = Validator().validate(extracted)

    # 3: Assess quality
    print("\n[3/4] Quality assessment…" if demo else "\n[3/4] Quality…")
    scores = QualityAssessor().assess(df)

    # 4: Dashboard
    print("\n[4/4] Rendering dashboard…")

    ## if dashboard file already exists, add suffix to avoid overwrite
    dashboard_path = os.path.join(save_dir, f"{company}_esg_quality_dashboard.png")
    suffix = 1
    while os.path.exists(dashboard_path):
        dashboard_path = os.path.join(save_dir, f"{company}_esg_quality_dashboard_{suffix}.png")
        suffix += 1
   # df = pd.DataFrame(df)
    Dashboard().render(validated_items=df, scores=scores, company=company, save_path=dashboard_path)

    # CSV export
    csv = os.path.join(save_dir, f"{company}_esg_data.csv")
    suffix = 1
    while os.path.exists(csv):
        csv = os.path.join(save_dir, f"{company}_esg_data_{suffix}.csv")
        suffix += 1
    df = pd.DataFrame(df)
    df.to_csv(csv, index=False, encoding="utf-8-sig")
    print(f"  ✓ CSV → {csv}")

    print("\n" + "=" * 60)
    print("  ✓ Pipeline Complete")
    print("=" * 60)
    return df, scores



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=str, help="Path to ESG PDF report")
    ap.add_argument("--backend", default="ollama",
                    choices=["ollama","hf","groq","together","huggingface","openai"])
    ap.add_argument("--model", type=str, default=None)
    ap.add_argument("--api_key", type=str)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--company", default="Samsung Electronics")
    ap.add_argument("--output_dir", default="./esg_quality_dashboard")
    args = ap.parse_args()

    if not args.demo and not args.pdf:
        print("No PDF specified — running demo mode.\n")
        args.demo = True

    run_pipeline(args.pdf, args.api_key, args.demo,
                 args.company, args.output_dir)