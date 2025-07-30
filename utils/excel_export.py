import pandas as pd
from io import BytesIO

def export_volvo_to_excel_bytes(data):
    if not data:
        return None
    df = pd.DataFrame(data)
    for col in ["period_start", "period_end", "invoice_date", "payment_due", "performance_date"]:
        try:
            df[col] = pd.to_datetime(df[col], format="%d-%m-%Y")
        except Exception:
            df[col] = df[col]
            
    df["net"] = (
        df["net"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )
    df["vat"] = (df["net"] * 0.27).round(0)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return output

def export_multialarm_to_excel_bytes(data):
    if not data:
        return None
    
    df = pd.DataFrame(data)
    for col in ["period_start", "period_end", "invoice_date", "payment_due", "performance_date"]:
        try:
            df[col] = pd.to_datetime(df[col], format="%Y.%m.%d")
        except Exception:
            df[col] = df[col]
    
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return output