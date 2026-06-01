import pandas as pd
from db import upsert_vin, lookup_vin

def import_from_excel(filepath: str) -> dict:
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        return {"error": str(e)}

    df.columns = [c.strip().upper() for c in df.columns]

    vin_col = next((c for c in df.columns if "VIN" in c), None)
    loc_col = next((c for c in df.columns if "LOC" in c or "CODE" in c), None)

    if not vin_col or not loc_col:
        return {"error": f"Cannot find VIN/Location columns. Found: {list(df.columns)}"}

    added = updated = skipped = 0
    errors = []

    for _, row in df.iterrows():
        vin = str(row[vin_col]).strip()
        loc = str(row[loc_col]).strip()

        if not vin or vin.upper() == "NAN":
            skipped += 1
            continue
        try:
            existing = lookup_vin(vin)
            upsert_vin(vin, loc)
            if existing:
                updated += 1
            else:
                added += 1
        except Exception as e:
            errors.append(f"{vin}: {e}")

    return {"added": added, "updated": updated, "skipped": skipped, "errors": errors}
