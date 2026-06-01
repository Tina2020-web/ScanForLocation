import pandas as pd
import os
from db import EXCEL_PATH, load_data, save_data

def import_from_excel(filepath: str) -> dict:
    """
    Merge uploaded Excel into existing VIN_To_LocationCode.xlsx
    - Same VIN + different location → UPDATE location
    - New VIN → ADD new record
    - Same VIN + same location → SKIP
    """
    # Load new file
    try:
        df_new = pd.read_excel(filepath)
    except Exception as e:
        return {"error": str(e)}

    # Normalize columns
    df_new.columns = [c.strip().upper() for c in df_new.columns]
    vin_col = next((c for c in df_new.columns if "VIN" in c), None)
    loc_col = next((c for c in df_new.columns if "LOC" in c or "CODE" in c), None)

    if not vin_col or not loc_col:
        return {"error": f"Cannot find VIN/Location columns. Found: {list(df_new.columns)}"}

    # Normalize new data
    df_new = df_new.rename(columns={vin_col: "VIN", loc_col: "LOCATION_CODE"})
    df_new["VIN"] = df_new["VIN"].astype(str).str.strip().str.upper()
    df_new["LOCATION_CODE"] = df_new["LOCATION_CODE"].astype(str).str.strip()
    df_new = df_new[["VIN", "LOCATION_CODE"]].dropna()
    df_new = df_new[df_new["VIN"] != "NAN"]

    # Load existing data
    df_existing = load_data()

    added = updated = skipped = 0

    for _, row in df_new.iterrows():
        vin = row["VIN"]
        loc = row["LOCATION_CODE"]

        if vin in df_existing["VIN"].values:
            old_loc = df_existing.loc[df_existing["VIN"] == vin, "LOCATION_CODE"].values[0]
            if old_loc != loc:
                # Same VIN, different location → UPDATE
                df_existing.loc[df_existing["VIN"] == vin, "LOCATION_CODE"] = loc
                updated += 1
            else:
                # Same VIN, same location → SKIP
                skipped += 1
        else:
            # New VIN → ADD
            new_row = pd.DataFrame([{"VIN": vin, "LOCATION_CODE": loc}])
            df_existing = pd.concat([df_existing, new_row], ignore_index=True)
            added += 1

    # Save merged data back to VIN_To_LocationCode.xlsx
    save_data(df_existing)

    return {
        "added":   added,
        "updated": updated,
        "skipped": skipped,
        "total":   len(df_existing),
        "errors":  []
    }
