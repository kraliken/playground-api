import pdfplumber
import io
import re


def extract_tax_ids_from_pdf(file_bytes: bytes, own_tax_id: str):
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        if not pdf.pages:
            raise ValueError("Üres vagy hibás PDF.")
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""
        tax_ids = re.findall(r"\d{8}-\d{1}-\d{2}", text)
        own_found = None
        partner_found = None
        for tid in tax_ids:
            if tid == own_tax_id:
                own_found = tid
            else:
                partner_found = tid
                break
    return own_found, partner_found
