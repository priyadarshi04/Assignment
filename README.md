#  Invoice Data Extraction using Python (Amazon + Flipkart)

This project is a Python-based tool to automatically extract key fields from **Amazon** and **Flipkart invoice PDFs**, and export them into a clean, tabular **Excel spreadsheet**.

---

##  Features

✅ Supports invoices from **Amazon** and **Flipkart**

✅ Extracts important invoice fields:
- Invoice ID  
- Order ID  
- Invoice Date  
- Seller  
- Product Name  
- Quantity  
- Unit Price  
- Total Amount  
- GST (%)  
- Platform  
- File Name

✅ Automatically overwrites the Excel output file (`Extracted_Invoices.xlsx`)  
✅ Handles multiline product descriptions  
✅ Cleans and formats data for analysis or record-keeping  

---

## 🗂️ Folder Structure

Invoice-Extractor/
│
├── Input/ → Place all .pdf invoice files here
│
├── Output/ → Output Excel file is saved here
│ └── Extracted_Invoices.xlsx
│
├── extract_invoices.py → Main Python script
└── README.md → Project documentation (this file)
