import fitz 
import pandas as pd
import os
import re
from datetime import datetime

# ---------- Configuration ----------
INPUT_DIR = "./Input"
OUTPUT_FILE = "./Output/Extracted_Invoices.xlsx"

# ---------- Helper Functions ----------
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_date(date_str):
    for fmt in ("%d-%m-%Y", "%d.%m.%Y", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str.strip()

def extract_common_fields(text, file_name):
    def extract(pattern, default=""):
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else default

    platform = "Amazon" if "amazon" in file_name.lower() or "Amazon" in text else "Flipkart"

    if platform == "Amazon":
        invoice_id = extract(r"Invoice Number\s*:\s*([A-Z0-9\-]+)", "Unknown")
        order_id = extract(r"Order Number\s*:\s*([0-9\-]+)", "Unknown")
        raw_date = extract(r"Invoice Date\s*:\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})", "")
        date = parse_date(raw_date)
        seller = extract(r"Sold By\s*:\s*(.*?)\n", "Unknown Seller")

        # Product name (multi-line safe)
        product_match = re.search(r"1\s+(.*?)HSN", text, re.DOTALL)
        product = product_match.group(1).replace('\n', ' ').strip() if product_match else "Unknown Product"

        qty = extract(r"\bQty\b\s*\n?\s*([0-9]+)", "1")
        unit_price = extract(r"\bUnit\s*Price\b\s*₹?(\d+\.\d{2})", "0.00").replace(",", "")

        # Total amount from 'Total: ₹xx ₹yy'
        total_match = re.search(r"Total:\s*₹[\d\.]+\s*₹(\d+\.\d{2})", text)
        if not total_match:
            total_match = re.search(r"Invoice Value\s*:\s*₹?(\d+\.\d{2})", text)
        total_amount = total_match.group(1) if total_match else unit_price

        #Combine CGST + SGST
        gst_rates = re.findall(r"(\d+)%\s+(?:CGST|SGST)", text)
        gst_percent = f"{sum(map(int, gst_rates))}%" if gst_rates else "0%"

    else:  #Flipkart
        invoice_id = extract(r"Invoice Number\s*[:#\-]?\s*([^\s\n#]+)", "Unknown")
        order_id = extract(r"Order ID\s*[:#\-]?\s*([A-Z0-9\-]+)", "Unknown")
        raw_date = extract(r"Invoice Date\s*[:\-]?\s*([0-9]{2}[./-][0-9]{2}[./-][0-9]{4})", "")
        date = parse_date(raw_date)
        seller = extract(r"Sold By\s*[:\-]?\s*(.*?)(?:,|Ship-from|GSTIN|\n)", "Unknown Seller")

        #product extraction
        lines = text.splitlines()
        product = "Unknown Product"
        for i, line in enumerate(lines):
            clean = line.strip()
            if (
                clean
                and not re.match(r"^\s*(Qty|Discount|Taxable|Total|IGST|SGST|CGST|Invoice|Order ID|Shipping|Handling).*", clean, re.IGNORECASE)
                and len(clean.split()) > 2
            ):
                next_lines = " ".join(lines[i:i+2])
                product = next_lines.strip()
                break

        qty = extract(r"Qty\s*[:\-]?\s*(\d+)", "1")
        unit_price = extract(r"(?:Taxable\s*value|Taxable Value)[^\d]*(\d+\.\d{2})", "0.00").replace(",", "")
        total_amount = extract(r"Grand Total\s*₹?\s*(\d+\.\d{2})", unit_price).replace(",", "")
        gst_match = re.search(r"(?:IGST|CGST|SGST)[^\d]*(\d+\.?\d*)\s*%", text)
        gst_percent = f"{gst_match.group(1)}%" if gst_match else "0%"

    return {
        "Invoice ID": invoice_id,
        "Order ID": order_id,
        "Invoice Date": date,
        "Seller": seller,
        "Product Name": product,
        "Quantity": qty,
        "Unit Price": f"₹{unit_price}",
        "Total Amount": f"₹{total_amount}",
        "GST (%)": gst_percent,
        "Platform": platform,
        "Invoice File Name": os.path.basename(file_name)
    }

# ---------- Main Logic ----------
def main():
    records = []
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Input folder not found: {INPUT_DIR}")
        return

    for file_name in os.listdir(INPUT_DIR):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(INPUT_DIR, file_name)
            print(f"📄 Processing {file_name}...")
            try:
                text = extract_text_from_pdf(file_path)
                data = extract_common_fields(text, file_name)
                records.append(data)
            except Exception as e:
                print(f"❌ Failed to process {file_name}: {e}")

    if records:
        df = pd.DataFrame(records)
        df.insert(0, 'S.No', range(1, len(df) + 1))
        columns_order = [
            "S.No", "Invoice ID", "Order ID", "Invoice Date", "Seller",
            "Product Name", "Quantity", "Unit Price", "Total Amount",
            "GST (%)", "Platform", "Invoice File Name"
        ]
        df = df[columns_order]
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"✅ Data extracted and saved to: {OUTPUT_FILE}")
    else:
        print("⚠️ No invoice data extracted.")

if __name__ == "__main__":
    main()
