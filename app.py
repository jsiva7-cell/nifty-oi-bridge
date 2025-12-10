from flask import Flask, jsonify
import pandas as pd
import os

app = Flask(__name__)

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
# Choose how to load data: STATIC (default), CSV, or SHEETS
DATA_MODE = os.getenv("DATA_MODE", "STATIC")  # STATIC | CSV | SHEETS
CSV_PATH = os.getenv("CSV_PATH", "zones.csv")
SHEETS_CSV_URL = os.getenv("SHEETS_CSV_URL", "")

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------
def safe_int(value, default=0):
    """Convert to int if numeric, else return default."""
    try:
        f = float(str(value).strip())
        return int(f)
    except (ValueError, TypeError):
        return default

def load_dataframe():
    """Load data based on DATA_MODE."""
    mode = DATA_MODE.upper()
    try:
        if mode == "STATIC":
            data = [
                {"CE_Zone": 22450, "PE_Zone": 22150, "Bias": "Neutral"},
                {"CE_Zone": 22520, "PE_Zone": 22240, "Bias": "Bullish"},
                {"CE_Zone": "Neutral", "PE_Zone": 22080, "Bias": "Bearish"},
            ]
            return pd.DataFrame(data), None

        if mode == "CSV":
            if not os.path.exists(CSV_PATH):
                return None, f"CSV not found at {CSV_PATH}"
            return pd.read_csv(CSV_PATH), None

        if mode == "SHEETS":
            if not SHEETS_CSV_URL:
                return None, "SHEETS_CSV_URL not set"
            return pd.read_csv(SHEETS_CSV_URL), None

        return None, f"Unknown DATA_MODE={DATA_MODE}"
    except Exception as e:
        return None, f"Load error: {str(e)}"

def normalize_dataframe(df):
    """Ensure required columns exist."""
    if "CE_Zone" not in df.columns:
        df["CE_Zone"] = 0
    if "PE_Zone" not in df.columns:
        df["PE_Zone"] = 0
    if "Bias" not in df.columns:
        df["Bias"] = "Neutral"
    return df

# -------------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------------
@app.route("/")
def home():
    return jsonify({"ok": True, "endpoints": ["/zones", "/zones/raw"], "mode": DATA_MODE})

@app.route("/zones")
def zones_json():
    df, err = load_dataframe()
    if err:
        return jsonify({"ok": False, "error": err}), 500

    df = normalize_dataframe(df)
    zones = []
    for _, row in df.iterrows():
        zones.append({
            "ce": safe_int(row.get("CE_Zone")),
            "pe": safe_int(row.get("PE_Zone")),
            "bias": str(row.get("Bias")) if pd.notna(row.get("Bias")) else "Neutral",
        })
    return jsonify({"ok": True, "count": len(zones), "zones": zones})

@app.route("/zones/raw")
def zones_raw():
    df, err = load_dataframe()
    if err:
        return jsonify({"ok": False, "error": err}), 500

    df = normalize_dataframe(df)
    return jsonify({"ok": True, "columns": df.columns.tolist(), "rows": df.to_dict(orient="records")})