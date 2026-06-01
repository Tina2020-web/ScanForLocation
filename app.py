from flask import Flask, request, jsonify, render_template
import os, tempfile, base64, json
import requests as http_requests
from db import init_db, lookup_vin, get_all, upsert_vin, delete_vin, EXCEL_PATH
from import_excel import import_from_excel

app = Flask(__name__)
init_db()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO  = os.environ.get("GITHUB_REPO", "Tina2020-web/ScanForLocation")
GITHUB_FILE  = "VIN_To_LocationCode.xlsx"
GITHUB_API   = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"

def get_github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def pull_excel_from_github():
    """Download latest Excel from GitHub before reading"""
    try:
        res = http_requests.get(GITHUB_API, headers=get_github_headers())
        if res.status_code == 200:
            content = res.json().get("content", "")
            file_bytes = base64.b64decode(content)
            with open(EXCEL_PATH, "wb") as f:
                f.write(file_bytes)
            print(f"[DEBUG] Pulled latest Excel from GitHub ✅")
            return True
    except Exception as e:
        print(f"[ERROR] Pull from GitHub failed: {e}")
    return False

def push_excel_to_github():
    """Push updated Excel back to GitHub via API"""
    try:
        # Get current file SHA (needed for update)
        res = http_requests.get(GITHUB_API, headers=get_github_headers())
        sha = res.json().get("sha") if res.status_code == 200 else None

        # Read updated Excel
        with open(EXCEL_PATH, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "message": "data: update VIN locations via web import",
            "content": content,
        }
        if sha:
            payload["sha"] = sha

        res = http_requests.put(GITHUB_API, headers=get_github_headers(), json=payload)
        if res.status_code in (200, 201):
            print(f"[DEBUG] Pushed Excel to GitHub ✅")
            return True
        else:
            print(f"[ERROR] Push failed: {res.status_code} {res.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Push to GitHub failed: {e}")
        return False

# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── API: Lookup ───────────────────────────────────────────────────────────────
@app.route("/api/lookup", methods=["GET"])
def api_lookup():
    vin = request.args.get("vin", "").strip()
    if not vin:
        return jsonify({"error": "VIN is required"}), 400
    result = lookup_vin(vin)
    if result:
        return jsonify({"found": True, "data": result})
    return jsonify({"found": False, "vin": vin})

# ── API: Records ──────────────────────────────────────────────────────────────
@app.route("/api/records", methods=["GET"])
def api_records():
    return jsonify(get_all())

# ── API: Upsert ───────────────────────────────────────────────────────────────
@app.route("/api/upsert", methods=["POST"])
def api_upsert():
    data = request.json
    vin = data.get("vin", "").strip()
    loc = data.get("location_code", "").strip()
    if not vin or not loc:
        return jsonify({"error": "vin and location_code required"}), 400
    upsert_vin(vin, loc)
    push_excel_to_github()
    return jsonify({"success": True})

# ── API: Delete ───────────────────────────────────────────────────────────────
@app.route("/api/delete", methods=["DELETE"])
def api_delete():
    vin = request.args.get("vin", "").strip()
    if not vin:
        return jsonify({"error": "VIN required"}), 400
    delete_vin(vin)
    push_excel_to_github()
    return jsonify({"success": True})

# ── API: Import ───────────────────────────────────────────────────────────────
@app.route("/api/import", methods=["POST"])
def api_import():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    if not f.filename.endswith((".xlsx", ".xls")):
        return jsonify({"error": "Only Excel files supported"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        f.save(tmp.name)
        result = import_from_excel(tmp.name)
    os.unlink(tmp.name)

    if "error" in result:
        return jsonify(result), 400

    # Push updated Excel to GitHub immediately
    pushed = push_excel_to_github()
    result["github_pushed"] = pushed

    return jsonify(result)

# ── API: Debug ────────────────────────────────────────────────────────────────
@app.route("/api/debug", methods=["GET"])
def api_debug():
    from db import load_data
    df = load_data()
    return jsonify({
        "excel_path":    EXCEL_PATH,
        "excel_exists":  os.path.exists(EXCEL_PATH),
        "total_records": len(df),
        "sample":        df.tail(5).to_dict(orient="records")
    })

# ── Startup: pull latest Excel from GitHub ───────────────────────────────────
with app.app_context():
    pull_excel_from_github()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)