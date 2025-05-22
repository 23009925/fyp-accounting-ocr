from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from pdf2image import convert_from_bytes
from PIL import Image
import torch
import gradio as gr
import re
import io

pending = "Pending"

# Initialize TrOCR model
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-stage1")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-stage1")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

receipt_store = []
report_store = []
last_parsed_receipt = {}

def extract_text_from_file(file_bytes):
    try:
        images = convert_from_bytes(file_bytes)
        results = []
        for image in images:
            pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
            generated_ids = model.generate(pixel_values)
            text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            results.append(text.strip())
        return "\n\n".join(results)
    except Exception as e:
        return f"❌ OCR Error: {str(e)}"

def parse_fields(text):
    # def extract(pattern, flags=0):
    #     match = re.search(pattern, text, re.IGNORECASE | flags)
    #     return match.group(1).strip() if match and match.group(1) else "Nil"
    def extract(pattern, flags=0):
        match = re.search(pattern, text, re.IGNORECASE | flags)
        group = match.group(1) if match else None
        return group.strip() if isinstance(group, str) else "Nil"

    return {
        "date_time": extract(r"Date[:\s]+(\d{2}/\d{2}/\d{4})"),
        "items": "See OCR text",
        "tax": extract(r"SGST.*?([\d,]+\.\d{2})"),
        "tip": "Nil",
        "total": extract(r"INVOICE TOTAL\s+([\d,]+)"),
        "category": extract(r"Dealers In[:\-\s]*([\w, &]+)"),
        "currency": "INR",
        "payment_method": "Advance Payment"
    }

def process_receipt(file):
    global last_parsed_receipt
    try:
        raw_text = extract_text_from_file(file)
        fields = parse_fields(raw_text)
        last_parsed_receipt = fields
        return fields["date_time"], fields["items"], fields["tax"], fields["tip"], fields["total"], fields["category"], fields["currency"], fields["payment_method"]
    except:
        return tuple(["Error"] * 8)

# def save_receipt(receipt_name_input):
#     if last_parsed_receipt:
#         last_parsed_receipt["custom_name"] = receipt_name_input.strip() if receipt_name_input.strip() else f"Receipt {len(receipt_store)+1}"
#         receipt_store.append(last_parsed_receipt)
#     return update_receipt_selector()

def save_receipt(receipt_name_input):
    if last_parsed_receipt:
        if isinstance(receipt_name_input, str) and receipt_name_input.strip():
            last_parsed_receipt["custom_name"] = receipt_name_input.strip()
        else:
            last_parsed_receipt["custom_name"] = f"Receipt {len(receipt_store)+1}"
        receipt_store.append(last_parsed_receipt)
    return update_receipt_selector()

def rename_receipt(index, new_name):
    try:
        index = int(index)
        if 0 <= index < len(receipt_store):
            receipt_store[index]["custom_name"] = new_name
    except:
        pass
    return update_receipt_selector()

def delete_receipt(index):
    try:
        index = int(index)
        if 0 <= index < len(receipt_store):
            receipt_store.pop(index)
    except:
        pass
    return update_receipt_selector()

def update_receipt_selector():
    choices = []
    for i, r in enumerate(receipt_store):
        label = f"{i}: {r.get('custom_name', r['date_time'])}"
        choices.append(label)
    return gr.update(choices=choices)

# def submit_report(name, selected_items):
#     try:
#         indices = [int(i.split(":")[0]) for i in selected_items]
#         selected = [receipt_store[i] for i in indices]
#         report_store.append({"name": name, "receipts": selected, "status": "Submitted", "Action": ""})
#         return update_report_table()
#     except Exception as e:
#         return gr.update(value=[["Error", 0, "Failed", str(e)]], headers=["Report Name", "# Receipts", "Status", "Action"])

def submit_report(name, selected_items):
    try:
        indices = [int(i.split(":")[0]) for i in selected_items]
        selected = [receipt_store[i] for i in indices]
        report_store.append({
            "name": name,
            "receipts": selected,
            "status": "Pending"
        })
        return update_report_table()
    except Exception as e:
        return gr.update(value=[["Error", 0, "Failed", str(e)]], headers=["Report Name", "# Receipts", "Status", "Action"])

def submit_to_accountant(index):
    try:
        index = int(index)
        if 0 <= index < len(report_store):
            report_store[index]["status"] = "Submitted"
    except:
        pass
    return update_report_table()


def submit_report(name, selected_items):
    try:
        indices = [int(i.split(":")[0]) for i in selected_items]
        selected = [receipt_store[i] for i in indices]
        report_store.append({"name": name, "receipts": selected, "status": pending})

        return update_report_table()
    except Exception as e:
        return gr.update(
            value=[["Error", 0, "Failed", str(e)]],
            headers=["Report Name", "# Receipts", "Status", "Action"]
        )

def update_report_table():
    headers = ["Report Name", "# Receipts", "Status", "Action"]
    rows = [[r["name"], len(r["receipts"]), r["status"], r["Action"]] for r in report_store]
    return gr.update(value=rows, headers=headers)

with gr.Blocks(css="""
.grey-box input,
.grey-box textarea,
.grey-box .wrap,
.grey-box .form,
.grey-box .checkbox,
.grey-box .dataframe,
.grey-box .scroll-hide {
    background-color: #f0f0f0 !important;
}
""") as demo:

    with gr.Column():
        gr.Markdown("## Receipt Upload & OCR")

        upload_file = gr.File(label="Upload Receipt", type="binary")

        with gr.Row():
            date_time = gr.Textbox(label="Document Date/Time", elem_classes=["grey-box"])
            items = gr.Textbox(label="Items", elem_classes=["grey-box"])
            tax = gr.Textbox(label="Tax", elem_classes=["grey-box"])
            tip = gr.Textbox(label="Tip", elem_classes=["grey-box"])
            total = gr.Textbox(label="Total", elem_classes=["grey-box"])

        category = gr.Textbox(label="Category", elem_classes=["grey-box"])
        currency = gr.Textbox(label="Currency", elem_classes=["grey-box"])

        with gr.Row():
            payment_method = gr.Textbox(label="Payment Method", elem_classes=["grey-box"])
            save_btn = gr.Button("Save")

        upload_file.change(
            fn=process_receipt,
            inputs=[upload_file],
            outputs=[date_time, items, tax, tip, total, category, currency, payment_method]
        )

        receipt_selector = gr.CheckboxGroup(label="Select Receipts", choices=[], elem_classes=["grey-box"])

    with gr.Column():
        gr.Markdown("### ✏ Edit Saved Receipts")
        edit_index = gr.Number(label="Receipt Index to Edit/Delete", elem_classes=["grey-box"])
        new_name = gr.Textbox(label="New Receipt Name", elem_classes=["grey-box"])
        rename_btn = gr.Button("Rename Receipt")
        delete_btn = gr.Button("Delete Receipt")

        rename_btn.click(fn=rename_receipt, inputs=[edit_index, new_name], outputs=[receipt_selector])
        delete_btn.click(fn=delete_receipt, inputs=[edit_index], outputs=[receipt_selector])
        save_btn.click(fn=save_receipt, outputs=[receipt_selector])

    with gr.Column():
        for idx, report in enumerate(report_store):
            with gr.Row():
                report_table = gr.Dataframe(headers=["Report Name", "# Receipts", "Status", "Action"], interactive=False, elem_classes=["grey-box"])
                gr.Markdown(f"**{report['name']}** | {len(report['receipts'])} receipts | Status: {report['status']}")
                gr.Button("Submit", elem_id=f"submit_{idx}").click(
                fn=submit_to_accountant,
                inputs=[gr.Textbox(value=str(idx), visible=False)],
                outputs=[report_table]
                )


    # with gr.Column():
    #     gr.Markdown("## 📋 Expense Reports")
    #     report_name = gr.Textbox(label="Report", elem_classes=["grey-box"])
    #     submit_report_btn = gr.Button("Submit")
    #     report_table = gr.Dataframe(headers=["Report Name", "# Receipts", "Status", "Action"], interactive=False, elem_classes=["grey-box"])

    #     submit_report_btn.click(fn=submit_report, inputs=[report_name, receipt_selector], outputs=[report_table])

demo.launch()