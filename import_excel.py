import pandas as pd
from db import load_data, save_data

def read_all_sheets(filepath: str) -> pd.DataFrame:
    """Read all sheets from Excel and combine into one DataFrame"""
    all_sheets = pd.read_excel(filepath, sheet_name=None)
    print(f"[DEBUG] Upload sheets found: {list(all_sheets.keys())}")

    frames = []
    for sheet_name, df in all_sheets.items():
        if df.empty:
            continue
        df.columns = [c.strip().upper() for c in df.columns]
        vin_col = next((c for c in df.columns if "VIN" in c), None)
        loc_col = next((c for c in df.columns if "LOC" in c or "CODE" in c), None)
        if not vin_col or not loc_col:
            print(f"[DEBUG] Sheet '{sheet_name}' skipped")
            continue
        df = df.rename(columns={vin_col: "VIN", loc_col: "LOCATION_CODE"})
        df["VIN"] = df["VIN"].astype(str).str.strip().str.upper()
        df["LOCATION_CODE"] = df["LOCATION_CODE"].astype(str).str.strip()
        df = df[["VIN", "LOCATION_CODE"]].dropna()
        df = df[df["VIN"] != "NAN"]
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=["VIN", "LOCATION_CODE"])
    return pd.concat(frames, ignore_index=True)

def import_from_excel(filepath: str) -> dict:
    """Merge uploaded Excel (all sheets) into existing data"""
    try:
        df_new = read_all_sheets(filepath)
    except Exception as e:
        return {"error": str(e)}

    if df_new.empty:
        return {"error": "No valid VIN/Location data found in any sheet"}

    df_existing = load_data()
    added = updated = skipped = 0

    for _, row in df_new.iterrows():
        vin = row["VIN"]
        loc = row["LOCATION_CODE"]

        if vin in df_existing["VIN"].values:
            old_loc = df_existing.loc[df_existing["VIN"] == vin, "LOCATION_CODE"].values[0]
            if old_loc != loc:
                df_existing.loc[df_existing["VIN"] == vin, "LOCATION_CODE"] = loc
                updated += 1
            else:
                skipped += 1
        else:
            new_row = pd.DataFrame([{"VIN": vin, "LOCATION_CODE": loc}])
            df_existing = pd.concat([df_existing, new_row], ignore_index=True)
            added += 1

    save_data(df_existing)

    return {
        "added":   added,
        "updated": updated,
        "skipped": skipped,
        "total":   len(df_existing),
        "errors":  []
    }
