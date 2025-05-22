# accountant_workflow.py

import pandas as pd
from data_store import receipt_store, statement_matches, report_status

def auto_match(row):
    for receipt in receipt_store:
        if str(receipt["date"]) == str(row.get("date")) and float(receipt["amount"]) == float(row.get("amount")):
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

def submit_report(df, mode):
    global report_status, statement_matches
    statement_matches = df.to_dict("records")
    report_status = "Submitted" if mode == "Submit" else "In Progress"
    return f"✅ Report {mode} successfully. Status: {report_status}"
