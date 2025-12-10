import io
import time
import requests
import pandas as pd
from flask import Flask, jsonify, Response

app = Flask(__name__)

# Your Google Sheet CSV export URL (tab gid=0 by default)
CSV_URL = "https://docs.google.com/spreadsheets/d/1gGfhOgQNKp6dTcps_uGOL2R2aCYewjKSlVyy8jkSulQ/export?format=csv&id=1gGfhOgQNKp6dTcps_uGOL2R2aCYewjKSlVyy8jkSulQ&gid=0"

def fetch_df():
    r = requests.get(CSV_URL, timeout=10)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))

@app.route("/")
def root():
    return jsonify({"ok": True, "endpoints": ["/zones", "/zones/raw"]})

@app.route("/zones")
def zones_json():
    # Returns a compact JSON payload with zones keyed by strike
    df = fetch_df()
    # Expect headers: strikePrice, CE.openInterest, PE.openInterest, CE_Zone, PE_Zone
    cols = ["strikePrice", "CE_Zone", "PE_Zone"]
    for c in cols:
        if c not in df.columns:
            return jsonify({"ok": False, "error": f"Missing column: {c}", "columns": df.columns.tolist()}), 400

    df = df[cols].copy()
    # Build {strike: {ce: int, pe: int}}
    data = {
        str(row["strikePrice"]): {
            "ce": int(row["CE_Zone"]) if pd.notna(row["CE_Zone"]) else 0,
            "pe": int(row["PE_Zone"]) if pd.notna(row["PE_Zone"]) else 0,
        }
        for _, row in df.iterrows()
    }
    return jsonify({
        "ok": True,
        "timestamp": int(time.time()),
        "count": len(df),
        "zones": data
    })

@app.route("/zones/raw")
def zones_raw_text():
    # Returns a simple newline text of CE_Zone values (one per row)
    df = fetch_df()
    if "CE_Zone" not in df.columns:
        return Response("ERROR: Missing CE_Zone column", mimetype="text/plain", status=400)
    values = df["CE_Zone"].fillna(0).astype(int).tolist()
    return Response("\n".join(map(str, values)), mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)