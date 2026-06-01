import os
import pandas as pd
from datetime import datetime

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "VIN_To_LocationCode.xlsx")

def load_data() -> pd.DataFrame:
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame(columns=["VIN", "LOCATION_CODE"])
    
    try:
        # Read ALL sheets
        all_sheets = pd.read_excel(EXCEL_PATH, sheet_name=None)
        print(f"[DEBUG] Found sheets: {list(all_sheets.keys())}")
    except Exception as e:
        print(f"[ERROR] Failed to read Excel: {e}")
        return pd.DataFrame(columns=["VIN", "LOCATION_CODE"])

    frames = []
    for sheet_name, df in all_sheets.items():
        if df.empty:
            continue
        df.columns = [c.strip().upper() for c in df.columns]
        vin_col = next((c for c in df.columns if "VIN" in c), None)
        loc_col = next((c for c in df.columns if "LOC" in c or "CODE" in c), None)
        if not vin_col or not loc_col:
            print(f"[DEBUG] Sheet '{sheet_name}' skipped - no VIN/LOC columns")
            continue
        df = df.rename(columns={vin_col: "VIN", loc_col: "LOCATION_CODE"})
        df["VIN"] = df["VIN"].astype(str).str.strip().str.upper()
        df["LOCATION_CODE"] = df["LOCATION_CODE"].astype(str).str.strip()
        df = df[["VIN", "LOCATION_CODE"]].dropna()
        df = df[df["VIN"] != "NAN"]
        print(f"[DEBUG] Sheet '{sheet_name}': {len(df)} records")
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=["VIN", "LOCATION_CODE"])

    # Combine all sheets, keep last occurrence of duplicate VINs
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["VIN"], keep="last")
    print(f"[DEBUG] Total combined records: {len(combined)}")
    return combined

def save_data(df: pd.DataFrame):
    df.to_excel(EXCEL_PATH, index=False, sheet_name="Data")

def init_db():
    pass  # No DB needed

def lookup_vin(vin: str):
    df = load_data()
    result = df[df["VIN"] == vin.strip().upper()]
    if result.empty:
        return None
    row = result.iloc[0]
    return {"vin": row["VIN"], "location_code": row["LOCATION_CODE"]}

def upsert_vin(vin: str, location_code: str):
    df = load_data()
    vin = vin.strip().upper()
    loc = location_code.strip()
    if vin in df["VIN"].values:
        df.loc[df["VIN"] == vin, "LOCATION_CODE"] = loc
    else:
        new_row = pd.DataFrame([{"VIN": vin, "LOCATION_CODE": loc}])
        df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)

def get_all():
    df = load_data()
    return df.to_dict(orient="records")

def delete_vin(vin: str):
    df = load_data()
    df = df[df["VIN"] != vin.strip().upper()]
    save_data(df)
