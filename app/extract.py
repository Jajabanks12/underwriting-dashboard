from __future__ import annotations
import os, re, json
from pathlib import Path
import pdfplumber
from pydantic import ValidationError
from schemas import Applicant


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def read_pdf_text(pdf_path: Path) -> str:
    """Try text-layer first. If nothing, return ''. (OCR optional later)"""
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                chunks.append(t)
    return "\n".join(chunks).strip()


def crude_parse(text: str) -> dict:
    """
    Cheap, deterministic parser to get you moving without an API.
    Replace with LLM later; keep the same output shape.
    """

    def find(pattern, cast=str):
        m = re.search(pattern, text, re.I)
        if not m:
            return None
        try:
            return cast(m.group(1))
        except:  # cast failed
            return None

    age = find(r"Age[:\s]+(\d{1,3})", int)
    city = find(r"City[:\s]+([A-Za-z .'-]+)")
    state = find(r"State[:\s]+([A-Z]{2})")
    zipc = find(r"Zip[:\s]+(\d{5})")
    revenue = find(r"Revenue[:\s]+\$?([\d,]+)", lambda s: float(s.replace(",", "")))
    naics = find(r"NAICS[:\s]+([\d]{4,6})")
    yib = find(r"Years\s*in\s*Business[:\s]+(\d{1,3})", int)
    zone = find(r"Zone[:\s]+([A-Z])")

    return {
        "applicant_id": "TEMP",
        "entity_type": "business" if yib is not None else "individual",
        "age": age,
        "years_in_business": yib,
        "naics": naics,
        "revenue_usd": revenue,
        "loss_runs_36mo": [],  # fill later
        "address": {"city": city, "state": state, "zip": zipc},
        "location_zone": zone,
        "prior_carrier": None,
        "requested_limits": {},
    }


def validate_to_model(payload: dict) -> Applicant:
    try:
        return Applicant(**payload)
    except ValidationError as e:
        # Return best-effort with missing pieces defaulted
        fixed = Applicant.model_validate(payload, strict=False)
        return fixed


def save_case_payload(case_dir: Path, raw_text: str, model: Applicant):
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "raw.txt").write_text(raw_text, encoding="utf-8")
    (case_dir / "extracted.json").write_text(model.model_dump_json(indent=2), encoding="utf-8")
