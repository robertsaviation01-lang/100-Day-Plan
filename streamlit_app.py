import json
import io
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data_backend as db
import dataroom

st.set_page_config(page_title="100-Day Plan - Team Dashboard", layout="wide")

# Initialize backend (Google Sheets if configured, else SQLite)
db.init_db()
db.load_initial_data_from_json()

# ── Dataroom: cached Drive API helpers ──────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_drive_service():
    try:
        sa_info = dict(st.secrets["gcp_service_account"])
        return dataroom.get_drive_service(sa_info)
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_dataroom_files(folder_id: str) -> list:
    svc = _get_drive_service()
    if svc is None:
        return []
    try:
        return dataroom.list_folder_files(svc, folder_id)
    except Exception:
        return []


def _upload_dataroom_file(folder_id: str, file_name: str, file_bytes: bytes, mime_type: str) -> bool:
    svc = _get_drive_service()
    if svc is None:
        return False
    try:
        uploaded = dataroom.upload_file_to_folder(
            svc,
            folder_id=folder_id,
            file_name=file_name,
            file_bytes=file_bytes,
            mime_type=mime_type or "application/octet-stream",
        )
        return bool(uploaded and uploaded.get("id"))
    except Exception:
        return False


ALLOWED_UPLOAD_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "csv",
    "ppt",
    "pptx",
    "txt",
    "zip",
    "png",
    "jpg",
    "jpeg",
}
MAX_UPLOAD_SIZE_MB = 50


def _validate_upload_file(upload_file):
    if not upload_file:
        return False, "Please choose a file to upload."

    file_name = upload_file.name or ""
    ext = Path(file_name).suffix.lower().lstrip(".")
    if not ext or ext not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        return False, f"Unsupported file type. Allowed: {allowed}"

    file_bytes = upload_file.getvalue()
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        return False, f"File is too large. Maximum size is {MAX_UPLOAD_SIZE_MB} MB."

    return True, ""


def render_dataroom_resources(
    label_folders: list,
    section_key: str,
    phase_id: str,
    tasks: list,
    key_prefix: str = "",
) -> None:
    """Render dataroom links and section-scoped manual attachments."""
    with st.expander("📁 Dataroom Resources", expanded=False):
        any_files = False
        for label, folder_id in label_folders:
            files = _fetch_dataroom_files(folder_id)
            if files:
                any_files = True
                st.markdown(f"**{label}**")
                for f in files:
                    st.markdown(f"- [{f['name']}]({f['webViewLink']})")

        manual_attachments = load_section_attachments(section_key, phase_id, tasks)
        if manual_attachments:
            st.markdown("**Manual Attachments**")
            for i, item in enumerate(manual_attachments):
                title = (item.get("name") or "Untitled Link").strip()
                url = (item.get("url") or "").strip()
                if url:
                    st.markdown(f"- [{title}]({url})")

        if not any_files and not manual_attachments:
            st.caption("No dataroom files found. Ensure the Drive API is enabled and the folder is shared with the service account.")

        can_edit = bool(st.session_state.user_name) and st.session_state.user_role in {"admin", "editor"}
        st.divider()
        st.caption("Attach a manual link when this section has no auto-synced Drive files, or to add additional references.")

        if not can_edit:
            st.caption("Login with admin/editor access to manage manual attachments.")
            return

        st.markdown("**Upload to Google Drive**")
        st.caption(f"Allowed types: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))} | Max size: {MAX_UPLOAD_SIZE_MB} MB")
        folder_options = {label: folder_id for label, folder_id in label_folders}
        selected_folder_label = st.selectbox(
            "Upload target folder",
            options=list(folder_options.keys()),
            key=f"upload_target_{key_prefix or section_key}",
        )
        upload_file = st.file_uploader(
            "Choose a file",
            type=sorted(ALLOWED_UPLOAD_EXTENSIONS),
            key=f"upload_file_{key_prefix or section_key}",
        )
        if st.button("Upload File", key=f"upload_btn_{key_prefix or section_key}"):
            valid, message = _validate_upload_file(upload_file)
            if not valid:
                st.warning(message)
            else:
                target_folder_id = folder_options[selected_folder_label]
                file_bytes = upload_file.getvalue()
                mime_type = upload_file.type or "application/octet-stream"

                progress = st.progress(0, text="Preparing upload...")
                progress.progress(25, text="Valid file. Starting upload to Google Drive...")

                with st.status("Uploading file", expanded=False) as status:
                    status.write(f"Uploading {upload_file.name}")
                    saved = _upload_dataroom_file(
                        target_folder_id,
                        upload_file.name,
                        file_bytes,
                        mime_type,
                    )
                    if saved:
                        progress.progress(85, text="Upload complete. Refreshing section...")
                        status.update(label="Upload complete", state="complete")
                    else:
                        status.update(label="Upload failed", state="error")

                if saved:
                    progress.progress(100, text="Done")
                    st.success("File uploaded to dataroom.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    progress.empty()
                    st.warning("Could not upload file. Check Drive permissions for the service account.")

        st.divider()

        add_form_key = f"add_manual_attachment_{key_prefix or section_key}"
        with st.form(add_form_key, clear_on_submit=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                link_name = st.text_input("Link name", key=f"link_name_{key_prefix or section_key}")
            with c2:
                link_url = st.text_input("Link URL", placeholder="https://...", key=f"link_url_{key_prefix or section_key}")
            add_clicked = st.form_submit_button("Attach Link")

        if add_clicked:
            link_name = (link_name or "").strip()
            link_url = (link_url or "").strip()
            if not link_name or not link_url:
                st.warning("Please provide both link name and URL.")
            elif not re.match(r"^https?://", link_url, flags=re.IGNORECASE):
                st.warning("Please enter a valid URL starting with http:// or https://")
            else:
                manual_attachments.append({"name": link_name, "url": link_url})
                if save_section_attachments(section_key, phase_id, tasks, manual_attachments, st.session_state.user_name):
                    st.success("Attachment saved.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Could not save attachment because no phase tasks were found.")

        if manual_attachments:
            options = list(range(len(manual_attachments)))
            remove_idx = st.selectbox(
                "Remove attachment",
                options,
                format_func=lambda idx: manual_attachments[idx].get("name") or f"Attachment {idx + 1}",
                key=f"remove_select_{key_prefix or section_key}",
            )
            if st.button("Remove Selected Attachment", key=f"remove_manual_attachment_{key_prefix or section_key}"):
                kept = [item for i, item in enumerate(manual_attachments) if i != remove_idx]
                if save_section_attachments(section_key, phase_id, tasks, kept, st.session_state.user_name):
                    st.success("Attachment removed.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Could not remove attachment because no phase tasks were found.")

GROUP_FORMATION_WORKSTREAMS = [
    {"id": "ws1", "name": "WS1 Ownership & Governance Setup", "phase_id": "phase1"},
    {"id": "ws2", "name": "WS2 Entity Formation (Ireland, US)", "phase_id": "phase2"},
    {"id": "ws3", "name": "WS3 Intercompany & Tax Architecture", "phase_id": "phase3"},
    {"id": "ws4", "name": "WS4 Regulatory Activation", "phase_id": "phase4"},
    {"id": "ws5", "name": "WS5 Governance & Data Room", "phase_id": "phase5"},
    {"id": "ws6", "name": "WS6 Operational Go-Live", "phase_id": "phase6"},
]

WORKSTREAM_DELIVERABLES = {
    "ws1": [
        "UK HoldCo incorporated",
        "Shares issued to co founders",
        "PSC register updated",
        "Governance framework established",
        "Shareholder agreement (optional)",
    ],
    "ws2": [
        "Ireland SPV incorporated (Fionnan Collins as Irish resident director)",
        "US HoldCo (Delaware LLC) incorporated with U.S. citizen Manager",
        "US OpCo (Texas Inc.) incorporated with U.S. Person for ITAR/EAR",
        "Bank accounts opened in each jurisdiction",
    ],
    "ws3": [
        "Master Intercompany Services Agreement (M ICSA)",
        "Schedules A-F (engineering, ops, treasury, shared services)",
        "Loan A/B agreements",
        "Licensing and cost sharing agreement",
        "Transfer Pricing Master File",
        "Local Files (Ireland, US, UK)",
        "Cost allocation keys",
    ],
    "ws4": [
        "FAA filings (8050 1, 8050 3, 8050 98, 8050 135)",
        "FAA Security Agreement (if applicable)",
        "ITAR/EAR compliance framework",
        "UK CAA Part NCC updates (SMS, ERP, MOR/ASR matrix)",
    ],
    "ws5": [
        "Full data room build (corporate, FAA, tax, treasury, engineering, safety)",
        "Board resolutions for all entities",
        "Delegation of Authority (DoA)",
        "Annual governance calendar",
        "Quarterly intercompany review process",
    ],
    "ws6": [
        "Intercompany billing activated",
        "Procurement and engineering workstreams launched",
        "MRO scheduling and supplier onboarding",
        "Insurance updates (values, loss payees)",
        "Risk register updated",
    ],
}

WORKSTREAM_OUTCOMES = {
    "ws1": "A clean, UK based parent entity for equity, governance, and investor alignment.",
    "ws2": "A fully formed multinational corporate structure with minimum personnel.",
    "ws3": "OECD aligned, audit ready intercompany framework.",
    "ws4": "Regulatory compliance across all jurisdictions.",
    "ws5": "Investor grade governance and documentation spine.",
    "ws6": "A fully operational, compliant, multinational aerospace group.",
}


def _deliverable_state_from_notes(ws_id, notes_text):
    if not notes_text:
        return {}
    pattern = rf"\[ws_deliverables:{ws_id}\](.*?)\[/ws_deliverables\]"
    match = re.search(pattern, notes_text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        state = json.loads(match.group(1).strip())
        return state if isinstance(state, dict) else {}
    except Exception:
        return {}


def load_workstream_deliverable_state(ws_id, phase_id, tasks):
    phase_tasks = sorted(
        [t for t in tasks if t.get("phase") == phase_id],
        key=lambda t: (t.get("startDay", 9999), t.get("name", "")),
    )
    for task in phase_tasks:
        state = _deliverable_state_from_notes(ws_id, task.get("notes", ""))
        if state:
            return state
    return {}


def save_workstream_deliverable_state(ws_id, phase_id, tasks, state, user_name):
    phase_tasks = sorted(
        [t for t in tasks if t.get("phase") == phase_id],
        key=lambda t: (t.get("startDay", 9999), t.get("name", "")),
    )
    if not phase_tasks:
        return False

    # Persist against one anchor task per phase to avoid duplicating metadata.
    anchor = phase_tasks[0]
    existing_notes = anchor.get("notes", "") or ""
    existing_notes = re.sub(
        rf"\[ws_deliverables:{ws_id}\].*?\[/ws_deliverables\]",
        "",
        existing_notes,
        flags=re.DOTALL,
    ).strip()
    state_block = f"[ws_deliverables:{ws_id}]" + json.dumps(state) + "[/ws_deliverables]"
    new_notes = (existing_notes + "\n" + state_block).strip()

    db.update_task(
        anchor["id"],
        status=anchor["status"],
        percent_complete=anchor.get("percentComplete", 0),
        notes=new_notes,
        user_name=user_name or "System",
    )
    return True


def _workstream_note_from_notes(ws_id, notes_text):
    if not notes_text:
        return ""
    pattern = rf"\[ws_note:{ws_id}\](.*?)\[/ws_note\]"
    match = re.search(pattern, notes_text, flags=re.DOTALL)
    if not match:
        return ""
    return (match.group(1) or "").strip()


def load_workstream_note(ws_id, phase_id, tasks):
    phase_tasks = sorted(
        [t for t in tasks if t.get("phase") == phase_id],
        key=lambda t: (t.get("startDay", 9999), t.get("name", "")),
    )
    for task in phase_tasks:
        note = _workstream_note_from_notes(ws_id, task.get("notes", ""))
        if note:
            return note
    return ""


def save_workstream_note(ws_id, phase_id, tasks, note_text, user_name):
    phase_tasks = sorted(
        [t for t in tasks if t.get("phase") == phase_id],
        key=lambda t: (t.get("startDay", 9999), t.get("name", "")),
    )
    if not phase_tasks:
        return False

    anchor = phase_tasks[0]
    existing_notes = anchor.get("notes", "") or ""
    existing_notes = re.sub(
        rf"\[ws_note:{ws_id}\].*?\[/ws_note\]",
        "",
        existing_notes,
        flags=re.DOTALL,
    ).strip()

    ws_note_block = ""
    if (note_text or "").strip():
        ws_note_block = f"[ws_note:{ws_id}]" + (note_text or "").strip() + "[/ws_note]"

    new_notes = "\n".join([part for part in [existing_notes, ws_note_block] if part]).strip()

    db.update_task(
        anchor["id"],
        status=anchor["status"],
        percent_complete=anchor.get("percentComplete", 0),
        notes=new_notes,
        user_name=user_name or "System",
    )
    return True


def _section_attachments_from_notes(section_key, notes_text):
    if not notes_text:
        return []
    pattern = rf"\[dataroom_manual:{re.escape(section_key)}\](.*?)\[/dataroom_manual\]"
    match = re.search(pattern, notes_text, flags=re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads((match.group(1) or "").strip())
    except Exception:
        return []
    if not isinstance(data, list):
        return []

    cleaned = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        url = str(item.get("url", "")).strip()
        if name and url:
            cleaned.append({"name": name, "url": url})
    return cleaned


def load_section_attachments(section_key, phase_id, tasks):
    phase_tasks = sorted(
        [t for t in tasks if t.get("phase") == phase_id],
        key=lambda t: (t.get("startDay", 9999), t.get("name", "")),
    )
    for task in phase_tasks:
        attachments = _section_attachments_from_notes(section_key, task.get("notes", ""))
        if attachments:
            return attachments
    return []


def save_section_attachments(section_key, phase_id, tasks, attachments, user_name):
    phase_tasks = sorted(
        [t for t in tasks if t.get("phase") == phase_id],
        key=lambda t: (t.get("startDay", 9999), t.get("name", "")),
    )
    if not phase_tasks:
        return False

    anchor = phase_tasks[0]
    existing_notes = anchor.get("notes", "") or ""
    existing_notes = re.sub(
        rf"\[dataroom_manual:{re.escape(section_key)}\].*?\[/dataroom_manual\]",
        "",
        existing_notes,
        flags=re.DOTALL,
    ).strip()

    cleaned = []
    for item in attachments or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        url = str(item.get("url", "")).strip()
        if name and url:
            cleaned.append({"name": name, "url": url})

    block = ""
    if cleaned:
        block = f"[dataroom_manual:{section_key}]" + json.dumps(cleaned) + "[/dataroom_manual]"

    new_notes = "\n".join([part for part in [existing_notes, block] if part]).strip()

    db.update_task(
        anchor["id"],
        status=anchor["status"],
        percent_complete=anchor.get("percentComplete", 0),
        notes=new_notes,
        user_name=user_name or "System",
    )
    return True


def compute_critical_summary(tasks, milestones):
    critical_tasks = sorted(
        [t for t in tasks if t.get("criticality") == "critical"],
        key=lambda t: t["startDay"],
    )
    projected_day = max((t["startDay"] + t["duration"] - 1 for t in critical_tasks), default=0)
    completed = sum(1 for t in critical_tasks if t["status"] == "Completed")
    at_risk = sum(1 for t in critical_tasks if t["status"] == "At Risk")
    next_critical = next((t for t in critical_tasks if t["status"] != "Completed"), None)

    milestone_rows = []
    for milestone in sorted(milestones, key=lambda m: m["day"]):
        linked_task = next((t for t in tasks if t["id"] == milestone.get("task_id")), None)
        status = "No linked task"
        if linked_task:
            status = f"{linked_task['status']} ({linked_task['percentComplete']}%)"
        milestone_rows.append(
            {
                "Day": milestone["day"],
                "Milestone": milestone["name"],
                "Linked Task Status": status,
            }
        )

    return {
        "critical_count": len(critical_tasks),
        "projected_day": projected_day,
        "completed": completed,
        "at_risk": at_risk,
        "next_critical": next_critical,
        "milestone_rows": milestone_rows,
    }


def compute_group_formation_workstreams(phases_list, tasks):
    workstream_meta = {
        "phase1": {"name": "SPV Activation (Day 0-20)", "window": "Day 0-20", "dependency": "None"},
        "phase2": {"name": "Intercompany Loan Execution (Day 15-35)", "window": "Day 15-35", "dependency": "SPV Activation"},
        "phase3": {"name": "Demonstrator Acquisition & PMI (Day 30-70)", "window": "Day 30-70", "dependency": "Loan A"},
        "phase4": {"name": "BEST Procurement & Engineering (Day 35-100)", "window": "Day 35-100", "dependency": "Loan B"},
        "phase5": {"name": "UK OpCo Demonstrator Programme Setup (Day 40-100)", "window": "Day 40-100", "dependency": "Loan C + Demonstrator PMI"},
        "phase6": {"name": "Governance & Compliance (Day 0-100)", "window": "Day 0-100", "dependency": "Parallel"},
    }

    rows = []
    for phase in phases_list:
        phase_id = phase.get("id", "")
        if phase_id not in workstream_meta:
            continue

        phase_tasks = [t for t in tasks if t.get("phase") == phase_id]
        total_tasks = len(phase_tasks)
        completed_tasks = sum(1 for t in phase_tasks if t.get("status") == "Completed")
        at_risk_tasks = sum(1 for t in phase_tasks if t.get("status") == "At Risk")
        in_progress_tasks = sum(1 for t in phase_tasks if t.get("status") == "In Progress")
        avg_complete = (
            sum(t.get("percentComplete", 0) for t in phase_tasks) / total_tasks if total_tasks else 0
        )

        rows.append(
            {
                "phase_id": phase_id,
                "workstream": workstream_meta[phase_id]["name"],
                "window": workstream_meta[phase_id]["window"],
                "dependency": workstream_meta[phase_id]["dependency"],
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "at_risk_tasks": at_risk_tasks,
                "avg_complete": avg_complete,
                "tasks": phase_tasks,
            }
        )

    return rows


def build_group_workstream_rows(tasks):
    rows = []
    for ws in GROUP_FORMATION_WORKSTREAMS:
        phase_tasks = [t for t in tasks if t.get("phase") == ws["phase_id"]]
        deliverables = WORKSTREAM_DELIVERABLES.get(ws["id"], [])
        deliverable_state = load_workstream_deliverable_state(ws["id"], ws["phase_id"], tasks)
        total_deliverables = len(deliverables)
        completed_deliverables = sum(1 for i in range(total_deliverables) if deliverable_state.get(str(i), False))
        deliverable_pct = (
            round((completed_deliverables / total_deliverables) * 100)
            if total_deliverables
            else 0
        )

        if any(t.get("status") == "At Risk" for t in phase_tasks):
            status = "At Risk"
        elif total_deliverables > 0 and completed_deliverables == total_deliverables:
            status = "Completed"
        elif completed_deliverables > 0:
            status = "In Progress"
        else:
            status = "Not Started"

        rows.append(
            {
                "Task": ws["name"],
                "Status": status,
                "Completion": f"{deliverable_pct}%",
                "Deliverables": f"{completed_deliverables}/{total_deliverables}",
                "Days": "0-5",
                "Critical": "🔴",
                "phase_id": ws["phase_id"],
            }
        )
    return rows


def create_gantt_chart(tasks, phases_list, milestones):
    fig = go.Figure()

    phase_colors = {}
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    for i, phase in enumerate(phases_list):
        phase_colors[phase["id"]] = colors[i % len(colors)]

    for task in tasks:
        base_date = datetime(2026, 4, 17)
        task_start = base_date + timedelta(days=task["startDay"] - 1)
        duration_ms = task["duration"] * 24 * 60 * 60 * 1000

        fig.add_trace(
            go.Bar(
                y=[task["name"]],
                x=[duration_ms],
                base=[task_start],
                orientation="h",
                marker=dict(
                    color=phase_colors.get(task["phase"], "#1f77b4"),
                    line=dict(
                        color="#ffc107" if task["criticality"] == "critical" else "gray",
                        width=3 if task["criticality"] == "critical" else 1,
                    ),
                ),
                name=task["name"],
                hovertext=(
                    f"{task['name']}<br>Days {task['startDay']}-{task['startDay'] + task['duration'] - 1}"
                    f"<br>{task['status']}: {task['percentComplete']}%"
                ),
                hoverinfo="text",
            )
        )

    for milestone in milestones:
        milestone_date = datetime(2026, 4, 17) + timedelta(days=milestone["day"] - 1)
        fig.add_shape(
            type="line",
            x0=milestone_date,
            x1=milestone_date,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(color="#d32f2f", width=1, dash="dot"),
        )

    fig.update_layout(
        title="100-Day Execution Plan - Gantt Chart",
        xaxis_type="date",
        height=600,
        showlegend=False,
        hovermode="closest",
    )
    return fig


def find_acehawk_logo_path() -> Path | None:
    candidates = [
        "AceHawk.png",
        "AceHawk.jpg",
        "AceHawk.jpeg",
        "AceHawk.webp",
        "acehawk.png",
        "acehawk.jpg",
        "acehawk.jpeg",
        "acehawk.webp",
        "acehawk_logo.png",
        "acehawk-logo.png",
        "assets/AceHawk.png",
        "assets/acehawk.png",
        "assets/acehawk_logo.png",
        "assets/acehawk-logo.png",
    ]
    for relative_path in candidates:
        logo_path = Path(relative_path)
        if logo_path.exists():
            return logo_path
    return None


def get_setting(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        secret_value = st.secrets.get(name, default)
        return str(secret_value).strip()
    except Exception:
        return default


def is_valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip().lower()))


def owner_display(owner_email: str, allowed_users: list[dict]) -> str:
    lookup = (owner_email or "").strip().lower()
    if not lookup:
        return ""
    for user in allowed_users:
        if user.get("email", "").lower() == lookup:
            return user.get("first_name", lookup)
    return lookup


def resolve_owner_email(owner_value: str, allowed_users: list[dict]) -> str:
    raw = (owner_value or "").strip()
    if not raw:
        return ""

    lookup = raw.lower()
    for user in allowed_users:
        if user.get("email", "").lower() == lookup:
            return user.get("email", "")

    matches = [
        user.get("email", "")
        for user in allowed_users
        if str(user.get("first_name", "")).strip().lower() == lookup and user.get("active", False)
    ]
    return matches[0] if len(matches) == 1 else ""


def prepare_csv_import_rows(import_df: pd.DataFrame, tasks: list[dict], phases: dict[str, str], allowed_users: list[dict]) -> tuple[list[dict], list[str]]:
    required_columns = ["Task Name", "Phase", "Status", "% Complete", "Start Day", "Duration", "Criticality"]
    missing = [column for column in required_columns if column not in import_df.columns]
    if missing:
        return [], ["Missing required columns: " + ", ".join(missing)]

    phase_name_to_id = {name.lower(): phase_id for phase_id, name in phases.items()}
    task_lookup = {(task["name"].strip().lower(), task["phase"]): task for task in tasks}
    allowed_statuses = {"not started", "in progress", "completed", "at risk"}

    prepared_rows: list[dict] = []
    skipped: list[str] = []
    for row_number, (_, row) in enumerate(import_df.fillna("").iterrows(), start=2):
        task_name = str(row.get("Task Name", "")).strip()
        phase_name = str(row.get("Phase", "")).strip()
        if not task_name or not phase_name:
            skipped.append(f"Row {row_number}: missing Task Name or Phase")
            continue

        phase_id = phase_name_to_id.get(phase_name.lower())
        if not phase_id:
            skipped.append(f"Row {row_number}: unknown phase '{phase_name}'")
            continue

        task = task_lookup.get((task_name.lower(), phase_id))
        if not task:
            skipped.append(f"Row {row_number}: task '{task_name}' in phase '{phase_name}' not found")
            continue

        status = str(row.get("Status", "")).strip()
        if status.lower() not in allowed_statuses:
            skipped.append(f"Row {row_number}: invalid status '{status}'")
            continue

        try:
            percent_complete = max(0, min(100, int(float(row.get("% Complete", 0)))))
            start_day = max(0, int(float(row.get("Start Day", 0))))
            duration = max(0, int(float(row.get("Duration", 0))))
        except ValueError:
            skipped.append(f"Row {row_number}: invalid numeric field")
            continue

        criticality = str(row.get("Criticality", "normal")).strip().lower() or "normal"
        if criticality not in {"critical", "normal"}:
            criticality = "normal"

        owner = resolve_owner_email(str(row.get("Owner", "")), allowed_users)
        owner_input = str(row.get("Owner", "")).strip()
        if owner_input and not owner:
            skipped.append(f"Row {row_number}: owner '{owner_input}' not found uniquely in allowlist")
            continue

        prepared_rows.append(
            {
                "task_id": task["id"],
                "status": status,
                "percent_complete": percent_complete,
                "owner": owner,
                "start_day": start_day,
                "duration": duration,
                "criticality": criticality,
            }
        )

    return prepared_rows, skipped


@st.cache_data(ttl=10, show_spinner=False)
def get_cached_allowed_users() -> list[dict]:
    return db.get_allowed_users()


@st.cache_data(ttl=10, show_spinner=False)
def get_cached_backend_health() -> dict:
    return db.get_backend_health()


@st.cache_data(ttl=10, show_spinner=False)
def get_cached_dashboard_data() -> dict:
    phases_list = db.get_all_phases()
    tasks = db.get_all_tasks()
    milestones = db.get_milestones()
    allowed_users = db.get_allowed_users()
    return {
        "phases_list": phases_list,
        "tasks": tasks,
        "milestones": milestones,
        "allowed_users": allowed_users,
    }


if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "nav_section" not in st.session_state:
    st.session_state.nav_section = "Group Formation Progress"

logo_path = find_acehawk_logo_path()
header_col_logo, header_col_title = st.columns([1, 9])

with header_col_logo:
    if logo_path is not None:
        st.image(str(logo_path), width=144)

with header_col_title:
    st.markdown("## 100-Day Execution Plan Dashboard")
    st.markdown("**Team Collaboration • Real-time Updates • Audit Trail**")

company_email_domain = get_setting("COMPANY_EMAIL_DOMAIN", "").lower()
default_admin_email = get_setting("DEFAULT_ADMIN_EMAIL", "")

with st.sidebar:
    st.markdown("---")
    st.subheader("👤 Your Identity")
    if company_email_domain:
        st.caption(f"Company domain required: @{company_email_domain}")
    if st.session_state.user_email:
        st.success(f"Logged in as: **{st.session_state.user_email}**")
        st.caption(f"Role: {st.session_state.user_role}")
        if st.button("Logout"):
            st.session_state.user_name = None
            st.session_state.user_email = None
            st.session_state.user_role = None
            st.rerun()
    else:
        user_input = st.text_input("Enter company email:", placeholder="name@company.com")
        if user_input and st.button("Login"):
            candidate = user_input.strip().lower()
            if not is_valid_email(candidate):
                st.error("Enter a valid email address.")
            elif company_email_domain and candidate.split("@")[-1] != company_email_domain:
                st.error(f"Use your company email (@{company_email_domain}).")
            else:
                users = get_cached_allowed_users()
                if not users:
                    db.upsert_allowed_user(candidate, role="admin", active=True, added_by="Bootstrap")
                    st.cache_data.clear()
                allowed_user = db.get_allowed_user(candidate)
                if not allowed_user or not allowed_user.get("active", False):
                    st.error("Access denied. Your email is not active in Back Office.")
                else:
                    st.session_state.user_email = candidate
                    st.session_state.user_role = allowed_user.get("role", "viewer")
                    st.session_state.user_name = candidate
                    st.rerun()
    st.markdown("---")

if not st.session_state.user_email:
    st.info("Login with an approved company email to access the dashboard.")
    st.stop()

current_user = db.get_allowed_user(st.session_state.user_email)
if not current_user or not current_user.get("active", False):
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.warning("Your access is no longer active. Please contact an administrator.")
    st.stop()

st.session_state.user_role = current_user.get("role", st.session_state.user_role)

if not current_user.get("acknowledged_summary", False):
    st.markdown("---")
    st.header("Executive Summary")
    st.markdown(
        """
AceHawk is implementing a four jurisdiction, regulator aligned, tax efficient group structure to support aircraft ownership, engineering operations, funding flows, and multinational compliance.

The formation plan establishes:
- UK HoldCo as the UK parent entity (owned by the co founders)
- Ireland SPV as the funding gateway and treasury centre
- US HoldCo (Delaware LLC) as the FAA compliant aircraft owner
- US OpCo (Texas Inc.) as the engineering and technical services centre
- UK OpCo (existing) as the operational entity under UK CAA Part NCC

Formation Objectives

Strategic Objectives
- Establish a globally compliant corporate structure
- Enable aircraft ownership and registration under FAA rules
- Centralise funding and treasury in a tax efficient jurisdiction
- Create a low risk engineering centre in the U.S.
- Maintain UK operational control under CAA Part NCC
- Ensure OECD aligned transfer pricing and defensible intercompany flows

Regulatory Objectives
- FAA "actual control" compliance (U.S. citizen Manager)
- ITAR/EAR technical data compliance (U.S. Person)
- UK CAA Part NCC operational compliance
- Irish corporate governance and substance

Investor Objectives
- Clean ownership chain
- Clear risk allocation
- Transparent funding flows
- Audit ready documentation
        """
    )

    acknowledged = st.checkbox("I have read and understood the Executive Summary.")
    if st.button("Proceed to Dashboard", type="primary", disabled=not acknowledged):
        db.set_allowed_user_acknowledged(st.session_state.user_email, True)
        st.cache_data.clear()
        st.rerun()
    st.stop()

backend_health = get_cached_backend_health()
st.sidebar.caption(f"Backend: {backend_health['backend_name']}")
st.sidebar.caption(backend_health["backend_status"])

if backend_health["use_google_requested"] and backend_health["backend_name"] != "Google Sheets":
    failed_checks = [c["check"] for c in backend_health["checks"] if not c["ok"]]
    st.warning("Google Sheets mode is enabled, but the app is currently using fallback storage.")
    if failed_checks:
        st.caption("Fix these checks: " + ", ".join(failed_checks))
    if st.button("Open Backend Health", type="secondary"):
        st.session_state.nav_section = "Backend Health"
        st.rerun()

try:
    dashboard_data = get_cached_dashboard_data()
    phases_list = dashboard_data["phases_list"]
    phases = {p["id"]: p["name"] for p in phases_list}
    tasks = dashboard_data["tasks"]
    milestones = dashboard_data["milestones"]
    allowed_users = dashboard_data["allowed_users"]
except Exception as exc:
    st.error(f"Could not load dashboard data from Google Sheets right now: {exc}")
    st.stop()

st.sidebar.title("Navigation")
section = st.sidebar.radio(
    "Select Section:",
    [
        "Group Formation Progress",
        "Phase Tracker",
        "Task Updates",
        "Gantt Chart",
        "Board View",
        "Activity Log",
        "Team Stats",
        "Data Management",
        "Back Office",
        "Backend Health",
    ],
    key="nav_section",
)

if section == "Group Formation Progress":
    st.header("🏗️ Section I: Group Formation Progress - The AceHawk Group")
    st.caption("Six workstreams that form the AceHawk Group foundation.")
    st.subheader("Execution Plan")

    # Show Group Formation Workstreams as initial phase (Day 0-5)
    with st.expander("🏗️ Group Formation Workstreams (Day 0-5)", expanded=True):
        gf_rows = build_group_workstream_rows(tasks)
        gf_avg = sum(float(r["Completion"].replace("%", "")) for r in gf_rows) / len(gf_rows) if gf_rows else 0
        st.progress(gf_avg / 100, text=f"{gf_avg:.0f}% Complete")
        gf_df = pd.DataFrame([{k: v for k, v in row.items() if k != "phase_id"} for row in gf_rows])
        st.dataframe(gf_df, use_container_width=True, hide_index=True)
        render_dataroom_resources(
            dataroom.EXECUTION_PLAN_FOLDERS,
            section_key="execution_plan",
            phase_id="phase1",
            tasks=tasks,
            key_prefix="exec_plan",
        )

    st.markdown("### Deliverable Tracking (Board-ready Group Formation Plan, Chap 4)")
    for ws in GROUP_FORMATION_WORKSTREAMS:
        deliverables = WORKSTREAM_DELIVERABLES.get(ws["id"], [])
        saved_state = load_workstream_deliverable_state(ws["id"], ws["phase_id"], tasks)
        outcome = WORKSTREAM_OUTCOMES.get(ws["id"], "")

        with st.expander(f"Deliverables | {ws['name']}", expanded=False):
            current_state = {}
            for i, item in enumerate(deliverables):
                current_state[str(i)] = st.checkbox(
                    f"{i + 1}. {item}",
                    value=saved_state.get(str(i), False),
                    key=f"{ws['id']}_deliverable_{i}",
                )

            completed = sum(1 for checked in current_state.values() if checked)
            total = len(deliverables)
            pct = round((completed / total) * 100) if total else 0
            st.progress(pct / 100, text=f"{completed}/{total} Deliverables Complete ({pct}%)")
            if outcome:
                st.caption(f"Outcome: {outcome}")

            if st.button("Save Deliverable Progress", key=f"save_deliverables_{ws['id']}"):
                if not st.session_state.user_name:
                    st.warning("Please login to save updates.")
                elif st.session_state.user_role not in {"admin", "editor"}:
                    st.warning("You do not have edit access. Contact Back Office.")
                else:
                    saved = save_workstream_deliverable_state(
                        ws["id"],
                        ws["phase_id"],
                        tasks,
                        current_state,
                        st.session_state.user_name,
                    )
                    if saved:
                        st.success("Deliverable progress saved.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.warning("Could not save deliverables because no phase tasks were found.")

            ws_folders = dataroom.WORKSTREAM_DATAROOM_FOLDERS.get(ws["id"])
            if ws_folders:
                st.divider()
                render_dataroom_resources(
                    ws_folders,
                    section_key=ws["id"],
                    phase_id=ws["phase_id"],
                    tasks=tasks,
                    key_prefix=ws["id"],
                )

    # Then show the original execution plan phases
    for phase in phases_list:
        phase_tasks = [t for t in tasks if t["phase"] == phase["id"]]
        if not phase_tasks:
            continue
        with st.expander(f"{phase['name']}", expanded=False):
            avg_progress = sum(t["percentComplete"] for t in phase_tasks) / len(phase_tasks)
            st.progress(avg_progress / 100, text=f"{avg_progress:.0f}% Complete")
            df = pd.DataFrame(
                [
                    {
                        "Task": t["name"],
                        "Owner": owner_display(t.get("owner", ""), allowed_users),
                        "Status": t["status"],
                        "Completion": f"{t['percentComplete']}%",
                        "Days": f"{t['startDay']}-{t['startDay'] + t['duration'] - 1}",
                        "Critical": "🔴" if t["criticality"] == "critical" else "",
                    }
                    for t in phase_tasks
                ]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

elif section == "Phase Tracker":
    st.header("📌 Section II: Phase Progress Tracker")

    col1, col2 = st.columns(2)
    with col1:
        phase_filter = st.selectbox("Filter by Phase:", ["All"] + [p["name"] for p in phases_list])
    with col2:
        status_filter = st.selectbox(
            "Filter by Status:", ["All", "Not Started", "In Progress", "Completed", "At Risk"]
        )

    filtered_tasks = tasks
    if phase_filter != "All":
        phase_id = next(p["id"] for p in phases_list if p["name"] == phase_filter)
        filtered_tasks = [t for t in filtered_tasks if t["phase"] == phase_id]
    if status_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status_filter]

    for phase in phases_list:
        phase_tasks = [t for t in filtered_tasks if t["phase"] == phase["id"]]
        if not phase_tasks:
            continue
        with st.expander(f"📌 {phase['name']}", expanded=True):
            avg_progress = sum(t["percentComplete"] for t in phase_tasks) / len(phase_tasks)
            st.progress(avg_progress / 100, text=f"{avg_progress:.0f}% Complete")
            df = pd.DataFrame(
                [
                    {
                        "Task": t["name"],
                        "Owner": owner_display(t.get("owner", ""), allowed_users),
                        "Status": t["status"],
                        "Completion": f"{t['percentComplete']}%",
                        "Days": f"{t['startDay']}-{t['startDay'] + t['duration'] - 1}",
                        "Critical": "🔴" if t["criticality"] == "critical" else "",
                    }
                    for t in phase_tasks
                ]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

elif section == "Task Updates":
    st.header("✏️ Section III: Task Management & Updates")

    if not st.session_state.user_name:
        st.warning("⚠️ Please login to update tasks (see left sidebar)")
        st.stop()
    if st.session_state.user_role not in {"admin", "editor"}:
        st.warning("⚠️ Your account is read-only. Back Office can grant editor access.")
        st.stop()

    col1, col2, col3 = st.columns(3)

    task_options = [f"[Workstream] {ws['name']}" for ws in GROUP_FORMATION_WORKSTREAMS] + [t["name"] for t in tasks]

    with col1:
        task_name = st.selectbox("Select Task:", task_options)

    is_workstream = task_name.startswith("[Workstream] ")
    selected_workstream = None
    phase_tasks = []

    if is_workstream:
        ws_name = task_name.replace("[Workstream] ", "", 1)
        selected_workstream = next(ws for ws in GROUP_FORMATION_WORKSTREAMS if ws["name"] == ws_name)
        phase_tasks = [t for t in tasks if t["phase"] == selected_workstream["phase_id"]]
        if phase_tasks:
            default_percent = int(sum(t["percentComplete"] for t in phase_tasks) / len(phase_tasks))
            if any(t["status"] == "At Risk" for t in phase_tasks):
                default_status = "At Risk"
            elif all(t["status"] == "Completed" for t in phase_tasks):
                default_status = "Completed"
            elif any(t["status"] == "In Progress" for t in phase_tasks) or default_percent > 0:
                default_status = "In Progress"
            else:
                default_status = "Not Started"
        else:
            default_percent = 0
            default_status = "Not Started"
    else:
        task = next(t for t in tasks if t["name"] == task_name)
        default_status = task["status"]
        default_percent = task["percentComplete"]

    status_options = ["Not Started", "In Progress", "Completed", "At Risk"]
    active_allowed_users = [u for u in allowed_users if u.get("active", False)]
    owner_choices = [("", "Unassigned")] + [
        (u.get("email", ""), u.get("first_name", u.get("email", "")))
        for u in active_allowed_users
        if u.get("email")
    ]

    if is_workstream:
        owner_value = next((t.get("owner", "") for t in phase_tasks if t.get("owner")), "")
        if phase_tasks and any((t.get("owner", "") != owner_value) for t in phase_tasks):
            owner_value = ""
        default_notes = load_workstream_note(selected_workstream["id"], selected_workstream["phase_id"], tasks)
    else:
        owner_value = task.get("owner", "")
        default_notes = str(task.get("notes", "") or "")

    owner_values = [item[0] for item in owner_choices]
    owner_index = owner_values.index(owner_value) if owner_value in owner_values else 0

    with col2:
        status = st.selectbox(
            "Status:",
            status_options,
            index=status_options.index(default_status),
        )
    with col3:
        percent = st.slider("% Complete:", 0, 100, default_percent)

    selected_owner = st.selectbox(
        "Task Owner:",
        owner_values,
        index=owner_index,
        format_func=lambda value: next((label for option, label in owner_choices if option == value), value or "Unassigned"),
    )

    if is_workstream and selected_workstream is not None:
        phase_name = phases.get(selected_workstream["phase_id"], selected_workstream["phase_id"])
        st.info(f"This updates all tasks in phase: {phase_name}")

        ws_id = selected_workstream["id"]
        deliverables = WORKSTREAM_DELIVERABLES.get(ws_id, [])
        saved_state = load_workstream_deliverable_state(ws_id, selected_workstream["phase_id"], tasks)
        completed = sum(1 for i in range(len(deliverables)) if saved_state.get(str(i), False))
        total = len(deliverables)
        pct = round((completed / total) * 100) if total else 0

        st.markdown("### Workstream Deliverable Progress")
        c1, c2, c3 = st.columns(3)
        c1.metric("Completed", completed)
        c2.metric("Total", total)
        c3.metric("Completion", f"{pct}%")
        st.progress(pct / 100 if total else 0, text=f"{completed}/{total} deliverables complete")

        if deliverables:
            deliverable_rows = [
                {
                    "Deliverable": item,
                    "Done": "Yes" if saved_state.get(str(i), False) else "No",
                }
                for i, item in enumerate(deliverables)
            ]
            st.dataframe(pd.DataFrame(deliverable_rows), use_container_width=True, hide_index=True)

    notes_key = f"progress_notes_{selected_workstream['id']}" if is_workstream and selected_workstream else f"progress_notes_{task['id']}"
    notes = st.text_area(
        "Progress Notes:",
        value=default_notes,
        key=notes_key,
        placeholder="Add progress updates, blockers, or next steps...",
    )

    if st.button("💾 Save Task Update", type="primary"):
        try:
            if is_workstream:
                db.update_tasks_bulk(
                    [phase_task["id"] for phase_task in phase_tasks],
                    status,
                    percent,
                    "",
                    st.session_state.user_name,
                    selected_owner,
                )
                save_workstream_note(
                    selected_workstream["id"],
                    selected_workstream["phase_id"],
                    tasks,
                    notes,
                    st.session_state.user_name,
                )
                st.success(
                    f"✅ Updated workstream '{task_name}' across {len(phase_tasks)} tasks - logged by {st.session_state.user_name}"
                )
            else:
                db.update_tasks_bulk(
                    [task["id"]],
                    status,
                    percent,
                    notes,
                    st.session_state.user_name,
                    selected_owner,
                )
                st.success(f"✅ Updated '{task_name}' - logged by {st.session_state.user_name}")
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not save update: {exc}")

    st.subheader("📋 Update History")
    if is_workstream:
        recent = []
        for phase_task in phase_tasks:
            for item in db.get_task_history(phase_task["id"]):
                recent.append(
                    {
                        "Time": item["updated_at"],
                        "Task": phase_task["name"],
                        "User": item["user_name"],
                        "Status": item["status"],
                        "Progress": f"{item['percent_complete']}%",
                        "Notes": item["notes"],
                    }
                )
        recent = sorted(recent, key=lambda x: x["Time"], reverse=True)[:20]
        if recent:
            st.dataframe(pd.DataFrame(recent), use_container_width=True, hide_index=True)
        else:
            st.info("No updates yet for this workstream")
    else:
        history = db.get_task_history(task["id"])
        if history:
            history_df = pd.DataFrame(
                [
                    {
                        "Time": h["updated_at"],
                        "User": h["user_name"],
                        "Status": h["status"],
                        "Progress": f"{h['percent_complete']}%",
                        "Notes": h["notes"],
                    }
                    for h in history
                ]
            )
            st.dataframe(history_df, use_container_width=True, hide_index=True)
        else:
            st.info("No updates yet for this task")

elif section == "Gantt Chart":
    st.header("📅 Section IV: Gantt Chart - Timeline Visualization")
    summary = compute_critical_summary(tasks, milestones)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Projected Finish", f"Day {summary['projected_day']}")
    m2.metric("Critical Tasks", summary["critical_count"])
    m3.metric("Completed", summary["completed"])
    m4.metric("At Risk", summary["at_risk"])

    show_critical_only = st.checkbox("Show Critical Path Only")
    chart_tasks = [t for t in tasks if t["criticality"] == "critical"] if show_critical_only else tasks
    fig = create_gantt_chart(chart_tasks, phases_list, milestones)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pd.DataFrame(summary["milestone_rows"]), use_container_width=True, hide_index=True)

elif section == "Board View":
    st.header("📊 Section V: Board View - Executive Summary")
    summary = compute_critical_summary(tasks, milestones)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Projected Finish", f"Day {summary['projected_day']}")
    c2.metric("Critical Tasks", summary["critical_count"])
    c3.metric("Completed", summary["completed"])
    c4.metric("At Risk", summary["at_risk"])
    in_progress = len([t for t in tasks if t.get("criticality") == "critical" and t["status"] == "In Progress"])
    c5.metric("In Progress", in_progress)

elif section == "Activity Log":
    st.header("📋 Activity Log - Audit Trail")
    activity = db.get_activity_log(50)
    if activity:
        st.dataframe(pd.DataFrame(activity), use_container_width=True, hide_index=True)
    else:
        st.info("No activity yet")

elif section == "Team Stats":
    st.header("👥 Team Collaboration Statistics")
    stats = db.get_team_stats()
    col1, col2 = st.columns(2)
    col1.metric("Team Members", stats["total_users"])
    col2.metric("Total Updates", stats["total_updates"])
    if stats["top_contributors"]:
        st.dataframe(pd.DataFrame(stats["top_contributors"]), use_container_width=True, hide_index=True)

elif section == "Data Management":
    st.header("💾 Data Management")
    col1, col2 = st.columns(2)
    with col1:
        export_data = db.export_to_json()
        st.download_button(
            label="Download Plan as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"100_day_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )
    with col2:
        csv_data = "Task Name,Phase,Status,% Complete,Start Day,Duration,Criticality,Owner\n"
        for task in tasks:
            phase_name = phases.get(task["phase"], "Unknown")
            csv_data += (
                f'"{task["name"]}","{phase_name}","{task["status"]}",{task["percentComplete"]},'
                f'{task["startDay"]},{task["duration"]},{task["criticality"]},"{owner_display(task.get("owner", ""), allowed_users)}"\n'
            )
        st.download_button(
            label="Download Tasks as CSV",
            data=csv_data,
            file_name=f"100_day_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.subheader("Import Revised Tasks from CSV")
    st.caption("Use the exported CSV format. Matching is done by Task Name + Phase.")

    if st.session_state.user_role not in {"admin", "editor"}:
        st.info("CSV import is available to admin and editor accounts.")
    else:
        uploaded_csv = st.file_uploader("Upload revised tasks CSV", type=["csv"], key="tasks_csv_import")
        if uploaded_csv is not None:
            try:
                import_df = pd.read_csv(io.BytesIO(uploaded_csv.getvalue()))
                prepared_rows, skipped_rows = prepare_csv_import_rows(import_df, tasks, phases, allowed_users)

                col_a, col_b = st.columns(2)
                col_a.metric("Rows ready to import", len(prepared_rows))
                col_b.metric("Rows skipped", len(skipped_rows))

                if prepared_rows:
                    preview_df = pd.DataFrame(
                        [
                            {
                                "Task ID": row["task_id"],
                                "Status": row["status"],
                                "% Complete": row["percent_complete"],
                                "Owner": owner_display(row["owner"], allowed_users),
                                "Start Day": row["start_day"],
                                "Duration": row["duration"],
                                "Criticality": row["criticality"],
                            }
                            for row in prepared_rows[:20]
                        ]
                    )
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)

                if skipped_rows:
                    with st.expander("Skipped rows"):
                        for item in skipped_rows[:50]:
                            st.write(item)

                if prepared_rows and st.button("Import CSV Changes", type="primary"):
                    result = db.import_tasks_bulk(prepared_rows, st.session_state.user_email)
                    st.success(f"Imported {result.get('updated', 0)} task rows from CSV.")
                    st.cache_data.clear()
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not parse CSV: {exc}")

elif section == "Back Office":
    st.header("🔐 Back Office")
    st.caption("Manage who can access the dashboard using company email allowlist.")

    if st.session_state.user_role != "admin":
        st.error("Admin access required.")
        st.stop()

    st.info(
        "Company domain policy: "
        + (f"@{company_email_domain}" if company_email_domain else "No domain enforced (set COMPANY_EMAIL_DOMAIN to enforce)")
    )

    with st.form("add_allowed_user"):
        st.subheader("Add or Update User")
        new_email = st.text_input("Email", placeholder="name@company.com")
        new_first_name = st.text_input("First Name", placeholder="Damian")
        new_role = st.selectbox("Role", ["viewer", "editor", "admin"], index=0)
        new_active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button("Save User", type="primary")

    if submitted:
        candidate = (new_email or "").strip().lower()
        if not is_valid_email(candidate):
            st.error("Enter a valid email address.")
        elif company_email_domain and candidate.split("@")[-1] != company_email_domain:
            st.error(f"Email must match company domain @{company_email_domain}.")
        else:
            db.upsert_allowed_user(
                email=candidate,
                role=new_role,
                active=new_active,
                added_by=st.session_state.user_email,
                first_name=new_first_name,
            )
            st.success("User saved.")
            st.cache_data.clear()
            st.rerun()

    users = db.get_allowed_users()
    if users:
        users_df = pd.DataFrame(
            [
                {
                    "Email": u.get("email", ""),
                    "First Name": u.get("first_name", ""),
                    "Role": u.get("role", "viewer"),
                    "Active": "Yes" if u.get("active", False) else "No",
                    "Executive Summary Ack": "Yes" if u.get("acknowledged_summary", False) else "No",
                    "Added By": u.get("added_by", ""),
                    "Added At": u.get("added_at", ""),
                }
                for u in users
            ]
        )
        st.dataframe(users_df, use_container_width=True, hide_index=True)

        st.subheader("Manage Existing User")
        selected_email = st.selectbox("Select user", [u["email"] for u in users], key="bo_select_user")
        selected_user = next(u for u in users if u["email"] == selected_email)
        st.caption(
            "Executive Summary acknowledged: "
            + ("Yes" if selected_user.get("acknowledged_summary", False) else "No")
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            updated_first_name = st.text_input("First Name", value=selected_user.get("first_name", ""), key="bo_first_name")
            updated_role = st.selectbox(
                "Role",
                ["viewer", "editor", "admin"],
                index=["viewer", "editor", "admin"].index(selected_user.get("role", "viewer")),
                key="bo_role",
            )
            if st.button("Update Role"):
                db.upsert_allowed_user(
                    email=selected_email,
                    role=updated_role,
                    active=selected_user.get("active", True),
                    added_by=st.session_state.user_email,
                    first_name=updated_first_name,
                )
                st.success("User details updated.")
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("Set Active", type="secondary"):
                db.set_allowed_user_active(selected_email, True)
                st.success("User activated.")
                st.cache_data.clear()
                st.rerun()
        with col3:
            if st.button("Set Inactive", type="secondary"):
                if selected_email == st.session_state.user_email:
                    st.warning("You cannot deactivate your own active session.")
                else:
                    db.set_allowed_user_active(selected_email, False)
                    st.success("User deactivated.")
                    st.cache_data.clear()
                    st.rerun()
        with col4:
            if st.button("Reset Summary Ack", type="secondary"):
                db.set_allowed_user_acknowledged(selected_email, False)
                st.success("Executive Summary acknowledgement reset for selected user.")
                st.cache_data.clear()
                st.rerun()
    else:
        st.warning("No allowlisted users found.")

elif section == "Backend Health":
    st.header("🩺 Backend Health")
    st.caption("Validate Google Sheets configuration and confirm active backend connectivity.")

    health = db.get_backend_health()

    col1, col2 = st.columns(2)
    col1.metric("Active Backend", health["backend_name"])
    col2.metric("Google Mode Requested", "Yes" if health["use_google_requested"] else "No")

    st.info(health["backend_status"])

    checks_df = pd.DataFrame(
        [
            {
                "Check": item["check"],
                "Status": "PASS" if item["ok"] else "FAIL",
                "Details": item["details"],
            }
            for item in health["checks"]
        ]
    )
    st.dataframe(checks_df, use_container_width=True, hide_index=True)

    if st.button("Run Connectivity Test", type="primary"):
        result = db.run_connectivity_test()
        if result["ok"]:
            st.success(result["message"])
        else:
            st.error(result["message"])

    with st.expander("Expected Streamlit Secrets Format"):
        st.code(
            'USE_GOOGLE_SHEETS = "true"\n'
            'GOOGLE_SHEET_ID = "your_google_sheet_id"\n\n'
            '[gcp_service_account]\n'
            'type = "service_account"\n'
            'project_id = "..."\n'
            'private_key_id = "..."\n'
            'private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"\n'
            'client_email = "..."\n'
            'client_id = "..."\n'
            'auth_uri = "https://accounts.google.com/o/oauth2/auth"\n'
            'token_uri = "https://oauth2.googleapis.com/token"\n'
            'auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"\n'
            'client_x509_cert_url = "..."\n'
            'universe_domain = "googleapis.com"',
            language="toml",
        )
