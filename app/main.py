import streamlit as st
from pathlib import Path
from datetime import datetime
from sqlmodel import SQLModel, Session, create_engine, select
from db_init import engine, Case, Extract
from extract import read_pdf_text, crude_parse, validate_to_model, save_case_payload, DATA_DIR
from schemas import Applicant
from pathlib import Path
from rules_engine import evaluate_rules


st.set_page_config(page_title="Underwriting Dashboard", layout="wide")
st.title("Underwriting Dashboard — MVP")

# --- helpers ---
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "uw.db"


def get_session():
    return Session(engine)


tabs = st.tabs(["Inbox", "Case Detail", "Rules & Flags", "Risk & Pricing", "Audit Trail"])

with tabs[0]:
    st.subheader("Inbox")
    up = st.file_uploader("Drop a PDF (mock)", type=["pdf"])
    if up:
        # create a case record
        case_id = f"CASE-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        case_dir = DATA_DIR / case_id
        pdf_path = case_dir / up.name
        case_dir.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(up.read())

        # extract text
        text = read_pdf_text(pdf_path)
        if not text:
            st.warning("No text layer found (scanned PDF). OCR to be enabled later.")
        # parse and validate
        payload = crude_parse(text)
        model: Applicant = validate_to_model(payload)
        save_case_payload(case_dir, text, model)

        # persist minimal metadata to DB
        with get_session() as s:
            c = Case(
                external_id=case_id,
                status="extracted",
                created_ts=str(datetime.utcnow()),
                updated_ts=str(datetime.utcnow()),
            )
            s.add(c)
            s.commit()
            s.refresh(c)
            e = Extract(case_id=c.id, raw_text=text, json_blob=model.model_dump_json())
            s.add(e)
            s.commit()

        st.success(f"Created {case_id}")
        st.session_state["last_case_dir"] = str(case_dir)
        st.session_state["last_case_payload"] = model.model_dump()

with tabs[1]:
    st.subheader("Case Detail")
    if "last_case_payload" in st.session_state:
        data = st.session_state["last_case_payload"]
        st.write("**Extracted (editable):**")
        # simple edit form
        age = st.number_input("Age", value=int(data.get("age") or 0), min_value=0, max_value=120)
        entity_type = st.selectbox(
            "Entity Type",
            ["individual", "business"],
            index=0 if data.get("entity_type") == "individual" else 1,
        )
        city = st.text_input("City", value=(data.get("address") or {}).get("city") or "")
        state = st.text_input("State", value=(data.get("address") or {}).get("state") or "")
        zipc = st.text_input("Zip", value=(data.get("address") or {}).get("zip") or "")

        if st.button("Save Edits"):
            # update in-memory & on disk
            data["age"] = age or None
            data["entity_type"] = entity_type
            data["address"] = {"city": city, "state": state, "zip": zipc}
            model = validate_to_model(data)
            case_dir = Path(st.session_state["last_case_dir"])
            save_case_payload(case_dir, (case_dir / "raw.txt").read_text(encoding="utf-8"), model)
            st.session_state["last_case_payload"] = model.model_dump()
            st.success("Saved.")

with tabs[2]:
    st.subheader("Rules & Flags")
    if "last_case_payload" not in st.session_state:
        st.info("Upload a case first in the Inbox tab.")
    else:
        left, right = st.columns([1, 1])
        rules_file = Path(__file__).resolve().parents[1] / "rules" / "base.yaml"
        with left:
            st.caption(f"Using rules: {rules_file.name}")
            if st.button("Evaluate Rules", type="primary"):
                payload = st.session_state["last_case_payload"]
                result = evaluate_rules(payload, rules_file)
                st.session_state["last_rules_result"] = result

        if "last_rules_result" in st.session_state:
            res = st.session_state["last_rules_result"]
            st.markdown(f"**Rules Version:** `{res['rules_version']}`")
            st.markdown(
                f"**Passed:** {res['summary']['passed']}  |  **Failed:** {res['summary']['failed']}"
            )
            st.divider()
            for item in res["results"]:
                badge = "✅" if item["passed"] else "⚠️"
                st.markdown(
                    f"{badge} **{item['id']}** — *{item['severity']}*  \n{item['description']}  \n`{item['detail']}`"
                )
