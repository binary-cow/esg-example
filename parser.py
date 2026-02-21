try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
from typing import List, Dict, Optional
from tqdm import tqdm
# ============================================================
# 2. PDF PARSER
# ============================================================
class PDFParser:
    """
    Parses Korean ESG PDFs into page-level text and table data.
    """

    def __init__(self, pdf_path: str):
        if not PDF_AVAILABLE:
            raise ImportError("pdfplumber not installed.")
        self.pdf_path = pdf_path

    def parse(self) -> List[Dict]:
        pages = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in tqdm(enumerate(pdf.pages)):
                text = page.extract_text() or ""
                table_text = ""
                for table in (page.extract_tables() or []):
                    for row in table:
                        cells = [str(c) if c else "" for c in row]
                        table_text += " | ".join(cells) + "\n"
                combined = f"{text}\n\n[TABLE]\n{table_text}" if table_text else text
                pages.append({"page_num": i + 1, "text": text,
                              "table_text": table_text, "combined": combined})
        print(f"  ✓ Parsed {len(pages)} pages")
        return pages