import pdfplumber
import io
import re

def process_multialarm(pdf_bytes: bytes):

    full_text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += "\n" + page_text

    return full_text

def process_volvo(pdf_bytes: bytes):

    data = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:

        first_page_text = pdf.pages[0].extract_text()
        tables = pdf.pages[0].extract_tables()

        invoice_number = ""
        if tables and len(tables[0]) >= 2:
            row = tables[0][1]
            invoice_number = row[0]

        invoice_date = payment_due = performance_date = ""
        lines = first_page_text.splitlines()
        for line in lines:
            dates = re.findall(r"\d{2}-\d{2}-\d{4}", line)
            if len(dates) >= 3:
                invoice_date, payment_due, performance_date = dates[:3]
                break
        
        header_info = {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "payment_due": payment_due,
            "performance_date": performance_date
        }

        for page in pdf.pages:
            tables = page.extract_tables()
            if len(tables) >= 2:
                table = tables[1]

                for row in table:
                    flat_row = " ".join(row).replace('\n', ' ')
                    row_with_breaks = " ".join(row).split('\n')

                    license_plate = ""
                    if len(row_with_breaks) > 1:
                        after_newline = row_with_breaks[1]
                        match = re.search(r'(.+?)\s*\d{2}-\d{2}-\d{4}', after_newline)
                        if match:
                            raw_license = match.group(1)
                            license_plate = raw_license.replace(" ", "").replace("-", "")
                        # else:
                        #     license_plate = after_newline.split()[0].replace(" ", "").replace("-", "")

                    dates = re.findall(r"\d{2}-\d{2}-\d{4}", flat_row)
                    period_start = dates[0] if len(dates) > 0 else ""
                    period_end = dates[1] if len(dates) > 1 else ""

                    amounts = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", flat_row)
                    amount = amounts[-1] if amounts else ""

                    if period_start and license_plate and period_end and amount:
                        data.append({
                            **header_info,
                            "period_start": period_start,
                            "period_end": period_end,
                            "license_plate": license_plate,
                            "net": amount
                        })

    return data