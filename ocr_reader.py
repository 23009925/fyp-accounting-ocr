import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
import io
import filetype

def read_receipt_from_pdf(file_bytes):
    try:
        kind = filetype.guess(file_bytes)
        if not kind:
            return "❌ Could not detect file type."

        # Handle PDF
        if kind.extension == "pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            full_text = "\n\n".join(page.get_text() for page in doc)

            if full_text.strip():
                return f"🧾 Extracted using PyMuPDF:\n\n{full_text.strip()}"

            # fallback to OCR if PDF is scanned
            images = convert_from_bytes(file_bytes)
            results = []
            for image in images:
                text = pytesseract.image_to_string(image)
                results.append(text.strip())
            return f"🧾 Fallback OCR:\n\n" + "\n\n".join(results)

        # Handle image types
        elif kind.extension in ["jpg", "jpeg", "png"]:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            text = pytesseract.image_to_string(image)
            return f"🧾 Extracted from image:\n\n{text.strip()}"

        else:
            return f"❌ Unsupported file type: {kind.extension}"

    except Exception as e:
        return f"❌ OCR Error: {str(e)}"

