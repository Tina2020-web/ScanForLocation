# ScanForLocation — Requirements

## 1. Project Overview
A tool that scans a QR code (or barcode) containing a VIN (Vehicle Identification Number)
and returns the corresponding location code from the VIN-to-Location mapping table.
The mapping data is stored in a local database and can be updated at any time via Excel import.

---

## 2. Functional Requirements

### 2.1 QR Code / Barcode Scanning
- Scan a QR code or barcode image to extract the VIN number
- Support both image file input and live camera input

### 2.2 VIN to Location Lookup
- Look up the scanned VIN from the local database
- Return the corresponding Location Code
- Handle case where VIN is not found

### 2.3 Database Storage
- Store all VIN → Location Code mappings in a local SQLite database
- Support Create, Read, Update, Delete (CRUD) operations
- Persist data between sessions

### 2.4 Excel Import / Update
- Import `VIN_To_LocationCode.xlsx` into the database on first run
- Allow user to re-import an updated Excel file at any time
- Support **incremental update**: add new records, update changed records
- Detect and report duplicates or conflicts during import
- Show import summary (added / updated / skipped count)

### 2.5 Output
- Display the Location Code on screen after scan
- Optionally export current database to Excel/CSV

---

## 3. Non-Functional Requirements
- Offline capable (no internet required)
- Fast lookup (< 1 second)
- Easy to run on Windows
- Database update should not interrupt scanning operations

---

## 4. Tech Stack
- **Language**: Python 3
- **QR Scanning**: `opencv-python`, `pyzbar`
- **Excel Reading**: `pandas`, `openpyxl`
- **Database**: SQLite (via `sqlite3` built-in)
- **UI** (optional): `tkinter` for simple desktop UI

---

## 5. Dependencies (requirements.txt)
```
opencv-python
pyzbar
pandas
openpyxl
```

---

## 6. Database Schema

### Table: `vin_location`
| Column        | Type    | Description              |
|---------------|---------|--------------------------|
| id            | INTEGER | Primary key              |
| vin           | TEXT    | Vehicle Identification Number (unique) |
| location_code | TEXT    | Corresponding location code |
| updated_at    | TEXT    | Last updated timestamp   |

---

## 7. Excel Import Flow
```
Load Excel file
      ↓
For each row:
  ├─ VIN exists in DB? → Update location_code + updated_at
  └─ VIN not found?   → Insert new record
      ↓
Show summary: X added, Y updated, Z skipped
```

---

## 8. Input / Output

| Input | Output |
|-------|--------|
| QR code image / camera | VIN number |
| VIN number | Location Code (from DB) |
| Excel file | Updated database records |

---

## 9. File Structure
```
ScanForLocation/
├── QRcodeTest.jpg              # Sample QR code image
├── VIN_To_LocationCode.xlsx    # Source mapping file
├── vin_location.db             # SQLite database (auto-created)
├── requirements.md             # This file
├── requirements.txt            # Python dependencies
├── main.py                     # Main application (scan + lookup)
├── db.py                       # Database operations (CRUD)
└── import_excel.py             # Excel import / update logic
```
