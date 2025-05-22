# import pandas as pd
# import gradio as gr
# from data_store import receipt_store, statement_matches, report_status

# with gr.Column():
#     gr.Markdown("## Select Report to Match")
#     selected_report = gr.Dropdown(label="Submitted Reports", choices=[], interactive=True)
#     match_button = gr.Button("Match Expenses")

# def get_submitted_reports():
#     return [r["name"] for r in report_store if r["status"] == "Submitted"]



# def auto_match(row):
#     for receipt in receipt_store:
#         if str(receipt["date"]) == str(row.get("date")) and float(receipt["amount"]) == float(row.get("amount")):
#             return receipt
#     return "No Match"

# def parse_statement(file):
#     try:
#         if file.name.endswith(".xlsx"):
#             df = pd.read_excel(file)
#         elif file.name.endswith(".csv"):
#             df = pd.read_csv(file)
#         else:
#             return pd.DataFrame([{"Error": "Unsupported format"}])
        
#         df = df.rename(columns=lambda x: x.strip().lower())
#         df["match"] = df.apply(auto_match, axis=1)
#         df["comments"] = df["match"].apply(lambda m: m.get("notes", "") if isinstance(m, dict) else "")
#         return df
#     except Exception as e:
#         return pd.DataFrame([{"Error": str(e)}])

# def submit_report_interface(file, mode):
#     df = parse_statement(file)
#     global report_status, statement_matches
#     statement_matches = df.to_dict("records")
#     report_status = "Submitted" if mode == "Submit" else "In Progress"
#     return f"✅ Report {mode} successfully. Status: {report_status}", df

# # Gradio UI
# file_input = gr.File(label="📄 Upload Bank/Credit Card Statement (.csv or .xlsx)")
# mode_input = gr.Radio(choices=["Submit", "Save as Draft"], label="Select Action")
# output_text = gr.Textbox(label="Status Message")
# output_table = gr.Dataframe(label="Matched Statement with Comments")

# demo = gr.Interface(
#     fn=submit_report_interface,
#     inputs=[file_input, mode_input],
#     outputs=[output_text, output_table],
#     title="🧾 Accountant Workflow",
#     description="Upload a bank/credit card statement to automatically match with receipts and submit or save the report."
# )

# if __name__ == "__main__":

#     demo.launch(share=True)

# submit_report_btn.click(fn=submit_report, inputs=[report_name, receipt_selector], outputs=[report_table])
# submit_report_btn.click(fn=lambda: gr.update(choices=get_submitted_reports()), outputs=[selected_report])

import pandas as pd
import gradio as gr
from data_store import receipt_store, report_status, report_store, statement_matches

def get_submitted_reports():
    return [r["name"] for r in report_store if r["status"] == "Submitted"]

def auto_match(row):
    for receipt in receipt_store:
        if str(receipt.get("date")) == str(row.get("date")) and float(receipt.get("amount", 0)) == float(row.get("amount", 0)):
            return receipt
    return "No Match"

def parse_statement(file):
    try:
        if file.name.endswith(".xlsx"):
            df = pd.read_excel(file)
        elif file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            return pd.DataFrame([{"Error": "Unsupported format"}])
        
        df = df.rename(columns=lambda x: x.strip().lower())
        df["match"] = df.apply(auto_match, axis=1)
        df["comments"] = df["match"].apply(lambda m: m.get("notes", "") if isinstance(m, dict) else "")
        return df
    except Exception as e:
        return pd.DataFrame([{"Error": str(e)}])

def submit_report_interface(file, mode):
    df = parse_statement(file)
    global report_status, statement_matches
    statement_matches = df.to_dict("records")
    report_status = "Submitted" if mode == "Submit" else "In Progress"
    return f"✅ Report {mode} successfully. Status: {report_status}", df

with gr.Blocks() as demo:
    gr.Markdown("## 🧾 Accountant Workflow")

    with gr.Row():
        selected_report = gr.Dropdown(label="Submitted Reports", choices=get_submitted_reports(), interactive=True)
        match_button = gr.Button("Match Expenses")

    file_input = gr.File(label="📄 Upload Bank/Credit Card Statement (.csv or .xlsx)")
    mode_input = gr.Radio(choices=["Submit", "Save as Draft"], label="Select Action")
    output_text = gr.Textbox(label="Status Message")
    output_table = gr.Dataframe(label="Matched Statement with Comments")

    submit_button = gr.Button("Run Matching")

    submit_button.click(
        fn=submit_report_interface,
        inputs=[file_input, mode_input],
        outputs=[output_text, output_table]
    )

if __name__ == "__main__":
    demo.launch(share=True)
