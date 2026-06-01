from flask import Flask, request, jsonify, render_template
import os, tempfile
from db import init_db, lookup_vin, get_all, upsert_vin, delete_vin
from import_excel import import_from_excel

app = Flask(__name__)
init_db()

# ── Pages ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── API: Lookup VIN ──────────────────────────────────────────────────────────
@app.route("/api/lookup", methods=["GET"])
def api_lookup():
    vin = request.args.get("vin", "").strip()
    if not vin:
        return jsonify({"error": "VIN is required"}), 400
    result = lookup_vin(vin)
    if result:
        return jsonify({"found": True, "data": result})
    return jsonify({"found": False, "vin": vin})

# ── API: List all records ────────────────────────────────────────────────────
@app.route("/api/records", methods=["GET"])
def api_records():
    return jsonify(get_all())

# ── API: Manual add / update ─────────────────────────────────────────────────
@app.route("/api/upsert", methods=["POST"])
def api_upsert():
    data = request.json
    vin = data.get("vin", "").strip()
    loc = data.get("location_code", "").strip()
    if not vin or not loc:
        return jsonify({"error": "vin and location_code required"}), 400
    upsert_vin(vin, loc)
    return jsonify({"success": True})

# ── API: Delete ───────────────────────────────────────────────────────────────
@app.route("/api/delete", methods=["DELETE"])
def api_delete():
    vin = request.args.get("vin", "").strip()
    if not vin:
        return jsonify({"error": "VIN required"}), 400
    delete_vin(vin)
    return jsonify({"success": True})

# ── API: Upload Excel ─────────────────────────────────────────────────────────
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
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)