"""
services/document_parser.py - Multi-Format Document Intelligence Service
=========================================================================

Handles text and data extraction from uploaded medical documents:
  - PDFs: Local embedded text extraction via PyMuPDF (fitz); OCR fallback for scanned pages.
  - Images (PNG, JPG, JPEG): Local OCR via Tesseract (pytesseract).
  - Tabular (CSV, XLSX): Table preview parsing and column mapping.
  - Entity Extraction: Candidate lab results, glucose readings, report dates,
    and patient identity verification.

Safety & Integrity Guarantees:
  - Produces a reviewable draft only; does NOT automatically verify medical records.
  - Preserves source context and page numbers.
  - Warns on patient name mismatch between document and selected patient profile.
  - Reports dependency status clearly when OCR is unavailable instead of falsifying results.
"""

import os
import re
import csv
import io
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

# PyMuPDF
try:
    import fitz  # PyMuPDF
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False

# Pillow & pytesseract
try:
    from PIL import Image
    import pytesseract
    # Configure tesseract executable on Windows if not on system PATH
    tesseract_candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for cand in tesseract_candidates:
        if os.path.exists(cand):
            pytesseract.pytesseract.tesseract_cmd = cand
            break
    HAVE_TESSERACT = True
except ImportError:
    HAVE_TESSERACT = False


# Known common clinical lab test patterns with typical reference ranges and units
LAB_PATTERNS = [
    {
        "test_name": "HbA1c",
        "aliases": [r"\bhba1c\b", r"\bglycated\s+hemoglobin\b", r"\ba1c\b", r"\bhemoglobin\s+a1c\b"],
        "default_unit": "%",
        "default_range": "< 5.7%",
        "val_min": 3.0,
        "val_max": 20.0,
    },
    {
        "test_name": "Fasting Blood Glucose",
        "aliases": [r"\bfasting\s+blood\s+glucose\b", r"\bfasting\s+glucose\b", r"\bfbg\b", r"\bfbs\b"],
        "default_unit": "mg/dL",
        "default_range": "70 - 99 mg/dL",
        "val_min": 30.0,
        "val_max": 600.0,
    },
    {
        "test_name": "Random Blood Glucose",
        "aliases": [r"\brandom\s+blood\s+glucose\b", r"\brandom\s+glucose\b", r"\bblood\s+glucose\b"],
        "default_unit": "mg/dL",
        "default_range": "70 - 140 mg/dL",
        "val_min": 30.0,
        "val_max": 600.0,
    },
    {
        "test_name": "Total Cholesterol",
        "aliases": [r"\btotal\s+cholesterol\b", r"\bcholesterol,\s+total\b"],
        "default_unit": "mg/dL",
        "default_range": "< 200 mg/dL",
        "val_min": 50.0,
        "val_max": 500.0,
    },
    {
        "test_name": "HDL Cholesterol",
        "aliases": [r"\bhdl\s+cholesterol\b", r"\bhdl-c\b", r"\bhdl\b"],
        "default_unit": "mg/dL",
        "default_range": "> 40 mg/dL",
        "val_min": 10.0,
        "val_max": 150.0,
    },
    {
        "test_name": "LDL Cholesterol",
        "aliases": [r"\bldl\s+cholesterol\b", r"\bldl-c\b", r"\bldl\b"],
        "default_unit": "mg/dL",
        "default_range": "< 100 mg/dL",
        "val_min": 20.0,
        "val_max": 400.0,
    },
    {
        "test_name": "Triglycerides",
        "aliases": [r"\btriglycerides\b", r"\btg\b"],
        "default_unit": "mg/dL",
        "default_range": "< 150 mg/dL",
        "val_min": 20.0,
        "val_max": 1500.0,
    },
    {
        "test_name": "Serum Creatinine",
        "aliases": [r"\bserum\s+creatinine\b", r"\bcreatinine\b"],
        "default_unit": "mg/dL",
        "default_range": "0.6 - 1.2 mg/dL",
        "val_min": 0.2,
        "val_max": 15.0,
    },
    {
        "test_name": "eGFR",
        "aliases": [r"\begfr\b", r"\bestimated\s+gfr\b"],
        "default_unit": "mL/min/1.73m²",
        "default_range": "> 90 mL/min/1.73m²",
        "val_min": 5.0,
        "val_max": 200.0,
    },
    {
        "test_name": "Microalbumin",
        "aliases": [r"\bmicroalbumin\b", r"\burine\s+microalbumin\b", r"\balbumin/creatinine\s+ratio\b"],
        "default_unit": "mg/g",
        "default_range": "< 30 mg/g",
        "val_min": 1.0,
        "val_max": 1000.0,
    },
]


def is_ocr_available() -> bool:
    """Check if Tesseract binary and Python binding are accessible."""
    if not HAVE_TESSERACT:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _extract_text_from_pdf(source: Any) -> Tuple[str, int, bool, List[str]]:
    """
    Extracts text from a PDF file path or raw bytes.
    Falls back to Tesseract OCR if text layer is empty (scanned document).
    Returns (raw_text, page_count, ocr_used, warnings)
    """
    if not HAVE_FITZ:
        return "", 0, False, ["PyMuPDF library is unavailable for PDF extraction."]

    raw_text = ""
    warnings = []
    ocr_used = False

    try:
        if isinstance(source, bytes):
            doc = fitz.open(stream=source, filetype="pdf")
        else:
            doc = fitz.open(str(source))
        page_count = len(doc)
        pages_text = []

        for page_idx in range(page_count):
            page = doc[page_idx]
            p_text = page.get_text()
            if p_text and p_text.strip():
                pages_text.append(f"--- Page {page_idx + 1} ---\n" + p_text)
            else:
                # Scanned page: try OCR if available
                if is_ocr_available():
                    try:
                        pix = page.get_pixmap(dpi=200)
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        ocr_text = pytesseract.image_to_string(img)
                        if ocr_text.strip():
                            ocr_used = True
                            pages_text.append(f"--- Page {page_idx + 1} [OCR] ---\n" + ocr_text)
                    except Exception as e:
                        warnings.append(f"Page {page_idx + 1}: OCR execution error: {str(e)}")
                else:
                    warnings.append(
                        f"Page {page_idx + 1}: Scanned page detected with no text layer. "
                        "Tesseract OCR is not configured, so image text could not be extracted."
                    )

        raw_text = "\n\n".join(pages_text)
        doc.close()
        return raw_text, page_count, ocr_used, warnings
    except Exception as e:
        return "", 0, False, [f"Failed to read PDF document: {str(e)}"]


def _extract_text_from_image(source: Any) -> Tuple[str, bool, List[str]]:
    """Extract text from an image (file path or raw bytes) using Tesseract OCR."""
    if not is_ocr_available():
        return (
            "",
            False,
            [
                "Tesseract OCR engine is not available on this system. "
                "Install Tesseract-OCR and configure pytesseract to enable medical image text recognition."
            ],
        )

    try:
        if isinstance(source, bytes):
            img = Image.open(io.BytesIO(source))
        else:
            img = Image.open(str(source))
        text = pytesseract.image_to_string(img)
        if not text.strip():
            return "", True, ["OCR executed successfully but no recognizable text was detected in this image."]
        return text, True, []
    except Exception as e:
        return "", False, [f"Image OCR processing failed: {str(e)}"]


def _parse_tabular_file(source: Any, extension: str) -> Tuple[str, Dict[str, Any], List[str]]:
    """
    Parses CSV or XLSX (file path or raw bytes) into a preview dictionary and text representation.
    """
    warnings = []
    try:
        if isinstance(source, bytes):
            stream = io.BytesIO(source)
            if extension == ".csv":
                df = pd.read_csv(stream)
            elif extension == ".xlsx":
                df = pd.read_excel(stream)
            else:
                return "", {}, [f"Unsupported tabular format '{extension}'"]
        else:
            if extension == ".csv":
                df = pd.read_csv(source)
            elif extension == ".xlsx":
                df = pd.read_excel(source)
            else:
                return "", {}, [f"Unsupported tabular format '{extension}'"]

        total_rows = len(df)
        columns = [str(c) for c in df.columns]

        # Clean NaN values for JSON serializability
        preview_df = df.head(25).fillna("")
        sample_rows = preview_df.to_dict(orient="records")

        # Map candidate columns
        col_mappings = {}
        for c in columns:
            c_lower = c.lower().strip()
            if any(t in c_lower for t in ["time", "date", "timestamp", "recorded"]):
                col_mappings[c] = "timestamp"
            elif any(g in c_lower for t in ["glucose", "sugar", "value", "cgm", "mg/dl", "mmol"] for g in [t]):
                col_mappings[c] = "glucose_value"
            elif any(u in c_lower for u in ["unit"]):
                col_mappings[c] = "unit"
            elif any(t in c_lower for t in ["test", "panel", "analyte", "marker"]):
                col_mappings[c] = "test_name"
            elif any(r in c_lower for r in ["range", "reference"]):
                col_mappings[c] = "reference_range"

        preview = {
            "columns": columns,
            "total_rows": total_rows,
            "preview_rows": sample_rows,
            "suggested_mappings": col_mappings,
        }

        # Convert table to readable text summary
        text_summary = f"Tabular Data Table ({len(columns)} columns, {total_rows} rows):\n"
        text_summary += f"Columns: {', '.join(columns)}\n"
        text_summary += preview_df.to_string(index=False)

        return text_summary, preview, warnings
    except Exception as e:
        return "", {}, [f"Tabular parsing error: {str(e)}"]


def _extract_patient_name(text: str) -> Optional[str]:
    """Scan text for patient name patterns."""
    patterns = [
        r"(?:patient\s+name|patient|name|subject)\s*[:\-]\s*([A-Za-z\s]{2,40})",
        r"(?:name\s+of\s+patient)\s*[:\-]\s*([A-Za-z\s]{2,40})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Clean trailing newline or commas
            candidate = re.split(r"[\n,\r]", candidate)[0].strip()
            # Reject common header words
            if len(candidate) > 2 and not any(w in candidate.lower() for w in ["dob", "age", "male", "female", "report", "date"]):
                return candidate
    return None


def _extract_dates(text: str) -> List[str]:
    """Scan text for ISO, slash, or dash formatted collection/report dates."""
    date_patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{2}/\d{2}/\d{4}\b",
        r"\b\d{2}-\d{2}-\d{4}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
    ]
    dates = []
    for pat in date_patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        for m in matches:
            if m not in dates:
                dates.append(m)
    return dates[:5]


def _extract_candidate_labs(text: str, report_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """Scan document text for laboratory panel tests and measurements."""
    candidates = []
    lines = text.split("\n")

    for lab_def in LAB_PATTERNS:
        test_name = lab_def["test_name"]
        default_unit = lab_def["default_unit"]
        default_range = lab_def["default_range"]
        val_min = lab_def["val_min"]
        val_max = lab_def["val_max"]

        for line_no, line in enumerate(lines):
            # Check if any alias matches this line
            matched_alias = False
            for alias in lab_def["aliases"]:
                if re.search(alias, line, re.IGNORECASE):
                    matched_alias = True
                    break

            if not matched_alias:
                continue

            # Look for numbers on the same line or immediate context
            # Supports decimals like 7.4 or integers like 142
            numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", line)
            if not numbers:
                continue

            # Find candidate result value within range
            chosen_val = None
            for num_str in numbers:
                try:
                    val = float(num_str)
                    if val_min <= val <= val_max:
                        chosen_val = val
                        break
                except ValueError:
                    continue

            if chosen_val is None:
                continue

            # Unit detection
            unit = default_unit
            if "%" in line:
                unit = "%"
            elif "mg/dl" in line.lower():
                unit = "mg/dL"
            elif "mmol/l" in line.lower():
                unit = "mmol/L"
            elif "ml/min" in line.lower():
                unit = "mL/min/1.73m²"
            elif "mg/g" in line.lower():
                unit = "mg/g"

            # Reference range detection: look for e.g. < 5.7, 70-99, < 200, 0.6 - 1.2
            range_match = re.search(r"([<>]\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?)\s*(?:%|mg/dL|mmol/L)?", line)
            ref_range = range_match.group(1).strip() if range_match else default_range

            # Warnings
            warnings = []
            if unit == "mmol/L":
                warnings.append("Unit is in mmol/L; verify before saving.")
            if not range_match:
                warnings.append("Reference range was not explicitly found in line; default range applied.")

            # Construct measurement date
            measurement_date = report_date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")

            candidate = {
                "test_name": test_name,
                "result": chosen_val,
                "unit": unit,
                "reference_range": ref_range,
                "measurement_date": measurement_date,
                "confidence": 0.88 if range_match else 0.75,
                "source_line": line.strip()[:100],
                "warnings": warnings,
            }

            # Avoid adding duplicate of the same test if already found
            if not any(c["test_name"] == test_name for c in candidates):
                candidates.append(candidate)
                break  # take first strong match per test

    return candidates


def _extract_candidate_readings_from_table(table_preview: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract candidate time-series glucose readings from tabular uploads."""
    if not table_preview or "preview_rows" not in table_preview:
        return []

    mappings = table_preview.get("suggested_mappings", {})
    ts_col = next((c for c, m in mappings.items() if m == "timestamp"), None)
    val_col = next((c for c, m in mappings.items() if m == "glucose_value"), None)

    if not val_col:
        return []

    candidates = []
    for r in table_preview["preview_rows"][:20]:
        val_raw = r.get(val_col)
        ts_raw = r.get(ts_col) if ts_col else None
        try:
            val = float(val_raw)
            if 30 <= val <= 600:
                candidates.append({
                    "value": round(val, 1),
                    "unit": "mg/dL",
                    "timestamp": str(ts_raw) if ts_raw else datetime.now(timezone.utc).isoformat(),
                    "source_reference": "Tabular Row",
                    "confidence": 0.90,
                    "warnings": [],
                })
        except (ValueError, TypeError):
            continue

    return candidates


def parse_and_extract_document(
    file_source: Any,
    filename: Optional[str] = None,
    expected_patient_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main orchestration routine for extracting and structuring medical document contents.
    Accepts a filesystem Path/string or in-memory bytes (for S3 storage compatibility).

    Returns a comprehensive extraction dictionary:
      - raw_text: str
      - document_type: str ("pdf", "image", "tabular", "unknown")
      - page_count: int
      - table_preview: Optional[Dict]
      - extracted_patient_name: Optional[str]
      - patient_name_match: Optional[bool]
      - extracted_dates: List[str]
      - candidate_labs: List[Dict]
      - candidate_readings: List[Dict]
      - warnings: List[str]
      - ocr_used: bool
      - ocr_available: bool
    """
    if isinstance(file_source, (Path, str)):
        ext = Path(file_source).suffix.lower()
    else:
        ext = Path(filename or "").suffix.lower()

    raw_text = ""
    table_preview = None
    page_count = 1
    ocr_used = False
    warnings = []

    ocr_available = is_ocr_available()

    if ext == ".pdf":
        doc_type = "pdf"
        raw_text, page_count, ocr_used, pdf_warnings = _extract_text_from_pdf(file_source)
        warnings.extend(pdf_warnings)

    elif ext in [".png", ".jpg", ".jpeg"]:
        doc_type = "image"
        raw_text, ocr_used, img_warnings = _extract_text_from_image(file_source)
        warnings.extend(img_warnings)

    elif ext in [".csv", ".xlsx"]:
        doc_type = "tabular"
        raw_text, table_preview, tab_warnings = _parse_tabular_file(file_source, ext)
        warnings.extend(tab_warnings)

    else:
        doc_type = "unknown"
        warnings.append(f"Unsupported document format '{ext}'.")

    # Name extraction and verification
    extracted_name = _extract_patient_name(raw_text)
    name_match = None
    if extracted_name and expected_patient_name:
        # Normalize and compare
        norm_extracted = re.sub(r"\s+", " ", extracted_name.lower().strip())
        norm_expected = re.sub(r"\s+", " ", expected_patient_name.lower().strip())
        name_match = (norm_expected in norm_extracted or norm_extracted in norm_expected)
        if not name_match:
            warnings.append(
                f"PATIENT IDENTITY MISMATCH WARNING: Document header indicates patient '{extracted_name}', "
                f"which does not match the active target patient '{expected_patient_name}'. "
                "Explicit clinician confirmation is required before committing these records."
            )

    # Dates
    extracted_dates = _extract_dates(raw_text)
    primary_date = extracted_dates[0] if extracted_dates else None

    # Candidate labs
    candidate_labs = _extract_candidate_labs(raw_text, report_date_str=primary_date)

    # Candidate readings (from tabular or textual CGM logs)
    candidate_readings = []
    if table_preview:
        candidate_readings = _extract_candidate_readings_from_table(table_preview)

    if not candidate_labs and not candidate_readings and not warnings:
        warnings.append("No standard clinical laboratory markers or glucose series were automatically recognized. You may review raw text or manually map values.")

    return {
        "document_type": doc_type,
        "raw_text": raw_text[:8000],  # Bound text size in metadata to keep DB queries performant
        "page_count": page_count,
        "table_preview": table_preview,
        "extracted_patient_name": extracted_name,
        "patient_name_match": name_match,
        "extracted_dates": extracted_dates,
        "candidate_labs": candidate_labs,
        "candidate_readings": candidate_readings,
        "warnings": warnings,
        "ocr_used": ocr_used,
        "ocr_available": ocr_available,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }
