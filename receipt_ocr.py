# receipt_ocr.py

from data_store import receipt_store

def extract_receipt_data(file):
    # Dummy simulated OCR result — replace with your actual OCR logic
    receipt = {
        "id": f"R{len(receipt_store)+1:03}",
        "date": "2025-05-01",
        "amount": 120.50,
        "category": "Travel",
        "notes": "Taxi ride from OCR"
    }
    receipt_store.append(receipt)
    return receipt["date"], receipt["amount"], receipt["category"], receipt["notes"]
