"""
Hybrid data backend for 100-Day Plan.
Uses Google Sheets when configured, otherwise falls back to SQLite.
"""

import json
import os
import importlib
import tomllib
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import database as sqlite_db


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _column_letter(column_number: int) -> str:
    result = ""
    current = column_number
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


class SQLiteBackend:
    name = "SQLite"

    def init_db(self) -> None:
        sqlite_db.init_db()

    def load_initial_data_from_json(self) -> None:
        sqlite_db.load_initial_data_from_json()

    def get_all_phases(self) -> List[Dict[str, Any]]:
        return sqlite_db.get_all_phases()

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return sqlite_db.get_all_tasks()

    def get_milestones(self) -> List[Dict[str, Any]]:
        return sqlite_db.get_milestones()

    def update_task(self, task_id: str, status: str, percent_complete: int, notes: str, user_name: str = "Unknown") -> None:
        sqlite_db.update_task(task_id, status, percent_complete, notes, user_name)

    def update_task_owner(self, task_id: str, owner: str, user_name: str = "Unknown") -> None:
        sqlite_db.update_task_owner(task_id, owner, user_name)

    def update_tasks_bulk(self, task_ids: List[str], status: str, percent_complete: int, notes: str, user_name: str = "Unknown", owner: str = "") -> None:
        sqlite_db.update_tasks_bulk(task_ids, status, percent_complete, notes, user_name, owner)

    def import_tasks_bulk(self, rows: List[Dict[str, Any]], user_name: str = "Unknown") -> Dict[str, Any]:
        return sqlite_db.import_tasks_bulk(rows, user_name)

    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        return sqlite_db.get_task_history(task_id)

    def get_activity_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return sqlite_db.get_activity_log(limit)

    def get_activity_by_user(self, user_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        return sqlite_db.get_activity_by_user(user_name, limit)

    def export_to_json(self) -> Dict[str, Any]:
        return sqlite_db.export_to_json()

    def get_team_stats(self) -> Dict[str, Any]:
        return sqlite_db.get_team_stats()

    def ensure_default_admin(self, default_email: str) -> None:
        sqlite_db.ensure_default_admin(default_email)

    def get_allowed_users(self) -> List[Dict[str, Any]]:
        return sqlite_db.get_allowed_users()

    def get_allowed_user(self, email: str) -> Dict[str, Any] | None:
        return sqlite_db.get_allowed_user(email)

    def upsert_allowed_user(
        self,
        email: str,
        role: str,
        active: bool,
        added_by: str = "System",
        first_name: str = "",
        acknowledged_summary: Optional[bool] = None,
    ) -> None:
        sqlite_db.upsert_allowed_user(email, role, active, added_by, first_name, acknowledged_summary)

    def set_allowed_user_active(self, email: str, active: bool) -> None:
        sqlite_db.set_allowed_user_active(email, active)

    def set_allowed_user_acknowledged(self, email: str, acknowledged: bool = True) -> None:
        sqlite_db.set_allowed_user_acknowledged(email, acknowledged)


class GoogleSheetsBackend:
    name = "Google Sheets"

    def __init__(self, sheet_id: str, service_account_info: Dict[str, Any]) -> None:
        self.sheet_id = sheet_id
        gspread_mod = importlib.import_module("gspread")
        self.client = gspread_mod.service_account_from_dict(service_account_info)
        self.spreadsheet = self.client.open_by_key(sheet_id)
        self._worksheet_cache: Dict[str, Any] = {}
        self._read_cache: Dict[str, Any] = {}
        self._initialized = False
        self._initial_data_checked = False

    def _retry_google_call(self, fn, *args, **kwargs):
        """Retry transient Google Sheets quota errors with exponential backoff."""
        delays = [1.0, 2.0, 4.0, 8.0]
        for i, delay in enumerate(delays):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                # gspread APIError message includes HTTP status code; handle 429 quota throttling.
                if "429" in str(exc) and i < len(delays) - 1:
                    time.sleep(delay)
                    continue
                raise

    def _worksheet(self, title: str):
        ws = self._worksheet_cache.get(title)
        if ws is not None:
            return ws
        ws = self._retry_google_call(self.spreadsheet.worksheet, title)
        self._worksheet_cache[title] = ws
        return ws

    def _invalidate_read_cache(self) -> None:
        self._read_cache.clear()

    def _cached_read(self, key: str, loader, ttl_seconds: float = 3.0):
        now = time.time()
        cache_entry = self._read_cache.get(key)
        if cache_entry and cache_entry["expires_at"] > now:
            return cache_entry["value"]

        value = loader()
        self._read_cache[key] = {
            "value": value,
            "expires_at": now + ttl_seconds,
        }
        return value

    def _get_or_create_sheet(self, title: str, headers: List[str]):
        try:
            ws = self._worksheet(title)
        except Exception:
            ws = self._retry_google_call(
                self.spreadsheet.add_worksheet,
                title=title,
                rows=2000,
                cols=max(20, len(headers) + 2),
            )
            self._retry_google_call(ws.append_row, headers)
            self._worksheet_cache[title] = ws
            return ws
        return ws

    def _ensure_sheet_columns(self, title: str, required_headers: List[str]) -> List[str]:
        ws = self._worksheet(title)
        header = self._retry_google_call(ws.row_values, 1)
        current_headers = list(header)
        changed = False
        for required in required_headers:
            if required not in current_headers:
                current_headers.append(required)
                changed = True
        if changed:
            self._retry_google_call(ws.update, "A1", [current_headers])
        return current_headers

    def init_db(self) -> None:
        if self._initialized:
            return

        self._get_or_create_sheet("phases", ["id", "name", "order_num"])
        self._get_or_create_sheet(
            "tasks",
            [
                "id", "name", "phase", "start_day", "duration", "status", "percent_complete", "owner",
                "predecessors", "criticality", "created_at", "updated_at"
            ],
        )
        self._get_or_create_sheet("milestones", ["day", "name", "task_id"])
        self._get_or_create_sheet(
            "task_updates",
            ["task_id", "user_name", "status", "percent_complete", "notes", "updated_at"],
        )
        self._get_or_create_sheet("activity_log", ["user_name", "action", "task_id", "details", "created_at"])
        self._get_or_create_sheet(
            "allowed_users",
            ["email", "first_name", "role", "active", "acknowledged_summary", "added_by", "added_at"],
        )
        self._initialized = True

    def load_initial_data_from_json(self) -> None:
        if self._initial_data_checked:
            return

        tasks_ws = self._worksheet("tasks")
        existing_rows = len(self._retry_google_call(tasks_ws.get_all_records))
        if existing_rows > 0:
            self._initial_data_checked = True
            return

        json_file = Path(__file__).with_name("plan_data.json")
        if not json_file.exists():
            return

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        phases_ws = self._worksheet("phases")
        milestones_ws = self._worksheet("milestones")

        for phase in data.get("phases", []):
            self._retry_google_call(phases_ws.append_row, [
                phase.get("id", ""),
                phase.get("name", ""),
                phase.get("order", 0),
            ])

        now = _now_iso()
        for task in data.get("tasks", []):
            self._retry_google_call(tasks_ws.append_row, [
                task.get("id", ""),
                task.get("name", ""),
                task.get("phase", ""),
                task.get("startDay", 0),
                task.get("duration", 0),
                task.get("status", "Not Started"),
                task.get("percentComplete", 0),
                task.get("owner", ""),
                json.dumps(task.get("predecessors", [])),
                task.get("criticality", "normal"),
                now,
                now,
            ])

        for milestone in data.get("milestones", []):
            self._retry_google_call(milestones_ws.append_row, [
                milestone.get("day", 0),
                milestone.get("name", ""),
                milestone.get("taskId", ""),
            ])

        self._invalidate_read_cache()
        self._initial_data_checked = True

    def get_all_phases(self) -> List[Dict[str, Any]]:
        def _load_rows():
            ws = self._worksheet("phases")
            return self._retry_google_call(ws.get_all_records)

        rows = self._cached_read("phases_records", _load_rows)
        phases = []
        for row in rows:
            phases.append(
                {
                    "id": row.get("id", ""),
                    "name": row.get("name", ""),
                    "order_num": _to_int(row.get("order_num", 0)),
                }
            )
        return sorted(phases, key=lambda p: p["order_num"])

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        def _load_rows():
            ws = self._worksheet("tasks")
            return self._retry_google_call(ws.get_all_records)

        rows = self._cached_read("tasks_records", _load_rows)
        tasks: List[Dict[str, Any]] = []
        for row in rows:
            predecessors_raw = row.get("predecessors", "[]")
            if not predecessors_raw:
                predecessors = []
            else:
                try:
                    predecessors = json.loads(predecessors_raw)
                except json.JSONDecodeError:
                    predecessors = []
            tasks.append(
                {
                    "id": row.get("id", ""),
                    "name": row.get("name", ""),
                    "phase": row.get("phase", ""),
                    "startDay": _to_int(row.get("start_day", 0)),
                    "duration": _to_int(row.get("duration", 0)),
                    "status": row.get("status", "Not Started"),
                    "percentComplete": _to_int(row.get("percent_complete", 0)),
                    "owner": row.get("owner", ""),
                    "predecessors": predecessors,
                    "criticality": row.get("criticality", "normal"),
                    "created_at": row.get("created_at", ""),
                    "updated_at": row.get("updated_at", ""),
                }
            )
        return sorted(tasks, key=lambda t: t["startDay"])

    def get_milestones(self) -> List[Dict[str, Any]]:
        def _load_rows():
            ws = self._worksheet("milestones")
            return self._retry_google_call(ws.get_all_records)

        rows = self._cached_read("milestones_records", _load_rows)
        milestones: List[Dict[str, Any]] = []
        for row in rows:
            milestones.append(
                {
                    "day": _to_int(row.get("day", 0)),
                    "name": row.get("name", ""),
                    "task_id": row.get("task_id", ""),
                }
            )
        return sorted(milestones, key=lambda m: m["day"])

    def update_task(self, task_id: str, status: str, percent_complete: int, notes: str, user_name: str = "Unknown") -> None:
        tasks_ws = self._worksheet("tasks")
        ids = self._retry_google_call(tasks_ws.col_values, 1)
        if task_id not in ids:
            raise ValueError(f"Task ID not found: {task_id}")

        row_idx = ids.index(task_id) + 1
        header = self._retry_google_call(tasks_ws.row_values, 1)
        status_col = header.index("status") + 1
        percent_col = header.index("percent_complete") + 1
        updated_col = header.index("updated_at") + 1
        now = _now_iso()

        self._retry_google_call(tasks_ws.update_cell, row_idx, status_col, status)
        self._retry_google_call(tasks_ws.update_cell, row_idx, percent_col, percent_complete)
        self._retry_google_call(tasks_ws.update_cell, row_idx, updated_col, now)

        self._retry_google_call(self._worksheet("task_updates").append_row,
            [task_id, user_name, status, percent_complete, notes or "", now]
        )
        self._retry_google_call(self._worksheet("activity_log").append_row,
            [user_name, "Updated task", task_id, f"Status: {status}, Progress: {percent_complete}%", now]
        )
        self._invalidate_read_cache()

    def update_task_owner(self, task_id: str, owner: str, user_name: str = "Unknown") -> None:
        tasks_ws = self._worksheet("tasks")
        ids = self._retry_google_call(tasks_ws.col_values, 1)
        if task_id not in ids:
            raise ValueError(f"Task ID not found: {task_id}")

        row_idx = ids.index(task_id) + 1
        header = self._ensure_sheet_columns("tasks", ["owner"])
        owner_col = header.index("owner") + 1
        updated_col = header.index("updated_at") + 1 if "updated_at" in header else None
        now = _now_iso()

        self._retry_google_call(tasks_ws.update_cell, row_idx, owner_col, owner)
        if updated_col:
            self._retry_google_call(tasks_ws.update_cell, row_idx, updated_col, now)
        self._retry_google_call(
            self._worksheet("activity_log").append_row,
            [user_name, "Updated task owner", task_id, f"Owner: {owner or 'Unassigned'}", now],
        )
        self._invalidate_read_cache()

    def update_tasks_bulk(self, task_ids: List[str], status: str, percent_complete: int, notes: str, user_name: str = "Unknown", owner: str = "") -> None:
        if not task_ids:
            return

        tasks_ws = self._worksheet("tasks")
        header = self._ensure_sheet_columns("tasks", ["owner", "updated_at", "status", "percent_complete"])
        ids = self._retry_google_call(tasks_ws.col_values, 1)
        now = _now_iso()

        status_col = header.index("status") + 1
        percent_col = header.index("percent_complete") + 1
        owner_col = header.index("owner") + 1
        updated_col = header.index("updated_at") + 1

        data_updates = []
        task_update_rows = []
        activity_rows = []

        for task_id in task_ids:
            if task_id not in ids:
                raise ValueError(f"Task ID not found: {task_id}")

            row_idx = ids.index(task_id) + 1
            data_updates.extend(
                [
                    {"range": f"{_column_letter(status_col)}{row_idx}", "values": [[status]]},
                    {"range": f"{_column_letter(percent_col)}{row_idx}", "values": [[percent_complete]]},
                    {"range": f"{_column_letter(owner_col)}{row_idx}", "values": [[owner]]},
                    {"range": f"{_column_letter(updated_col)}{row_idx}", "values": [[now]]},
                ]
            )
            task_update_rows.append([task_id, user_name, status, percent_complete, notes or "", now])
            activity_rows.append([
                user_name,
                "Updated task",
                task_id,
                f"Status: {status}, Progress: {percent_complete}%, Owner: {owner or 'Unassigned'}",
                now,
            ])

        self._retry_google_call(tasks_ws.batch_update, data_updates)
        self._retry_google_call(self._worksheet("task_updates").append_rows, task_update_rows)
        self._retry_google_call(self._worksheet("activity_log").append_rows, activity_rows)
        self._invalidate_read_cache()

    def import_tasks_bulk(self, rows: List[Dict[str, Any]], user_name: str = "Unknown") -> Dict[str, Any]:
        if not rows:
            return {"updated": 0}

        tasks_ws = self._worksheet("tasks")
        header = self._ensure_sheet_columns(
            "tasks",
            ["status", "percent_complete", "owner", "start_day", "duration", "criticality", "updated_at"],
        )
        ids = self._retry_google_call(tasks_ws.col_values, 1)
        now = _now_iso()

        status_col = header.index("status") + 1
        percent_col = header.index("percent_complete") + 1
        owner_col = header.index("owner") + 1
        start_day_col = header.index("start_day") + 1
        duration_col = header.index("duration") + 1
        criticality_col = header.index("criticality") + 1
        updated_col = header.index("updated_at") + 1

        data_updates = []
        task_update_rows = []
        activity_rows = []
        updated = 0

        for row in rows:
            task_id = row["task_id"]
            if task_id not in ids:
                raise ValueError(f"Task ID not found: {task_id}")

            row_idx = ids.index(task_id) + 1
            data_updates.extend(
                [
                    {"range": f"{_column_letter(status_col)}{row_idx}", "values": [[row["status"]]]},
                    {"range": f"{_column_letter(percent_col)}{row_idx}", "values": [[row["percent_complete"]]]},
                    {"range": f"{_column_letter(owner_col)}{row_idx}", "values": [[row["owner"]]]},
                    {"range": f"{_column_letter(start_day_col)}{row_idx}", "values": [[row["start_day"]]]},
                    {"range": f"{_column_letter(duration_col)}{row_idx}", "values": [[row["duration"]]]},
                    {"range": f"{_column_letter(criticality_col)}{row_idx}", "values": [[row["criticality"]]]},
                    {"range": f"{_column_letter(updated_col)}{row_idx}", "values": [[now]]},
                ]
            )
            task_update_rows.append([task_id, user_name, row["status"], row["percent_complete"], "Imported from CSV", now])
            activity_rows.append([
                user_name,
                "Imported task from CSV",
                task_id,
                f"Status: {row['status']}, Progress: {row['percent_complete']}%, Owner: {row['owner'] or 'Unassigned'}",
                now,
            ])
            updated += 1

        self._retry_google_call(tasks_ws.batch_update, data_updates)
        self._retry_google_call(self._worksheet("task_updates").append_rows, task_update_rows)
        self._retry_google_call(self._worksheet("activity_log").append_rows, activity_rows)
        self._invalidate_read_cache()
        return {"updated": updated}

    def _get_task_updates_rows(self) -> List[Dict[str, Any]]:
        def _load_rows():
            ws = self._worksheet("task_updates")
            return self._retry_google_call(ws.get_all_records)

        return self._cached_read("task_updates_records", _load_rows)

    def _get_activity_rows(self) -> List[Dict[str, Any]]:
        def _load_rows():
            ws = self._worksheet("activity_log")
            return self._retry_google_call(ws.get_all_records)

        return self._cached_read("activity_records", _load_rows)

    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        rows = self._get_task_updates_rows()
        history = [
            {
                "user_name": r.get("user_name", ""),
                "status": r.get("status", ""),
                "percent_complete": _to_int(r.get("percent_complete", 0)),
                "notes": r.get("notes", ""),
                "updated_at": r.get("updated_at", ""),
            }
            for r in rows
            if r.get("task_id") == task_id
        ]
        return list(reversed(history[-20:]))

    def get_activity_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self._get_activity_rows()
        activity = [
            {
                "user_name": r.get("user_name", ""),
                "action": r.get("action", ""),
                "task_id": r.get("task_id", ""),
                "details": r.get("details", ""),
                "created_at": r.get("created_at", ""),
            }
            for r in rows
        ]
        return list(reversed(activity[-limit:]))

    def get_activity_by_user(self, user_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self.get_activity_log(5000)
        user_rows = [r for r in rows if r.get("user_name") == user_name]
        return user_rows[:limit]

    def export_to_json(self) -> Dict[str, Any]:
        return {
            "phases": self.get_all_phases(),
            "tasks": self.get_all_tasks(),
            "milestones": self.get_milestones(),
            "exported_at": _now_iso(),
        }

    def get_team_stats(self) -> Dict[str, Any]:
        updates = self._get_task_updates_rows()
        activity = self._get_activity_rows()

        users = sorted({r.get("user_name", "") for r in activity if r.get("user_name")})
        contributor_counts: Dict[str, int] = {}
        for row in activity:
            if row.get("action") != "Updated task":
                continue
            user = row.get("user_name", "")
            if not user:
                continue
            contributor_counts[user] = contributor_counts.get(user, 0) + 1

        top = sorted(contributor_counts.items(), key=lambda item: item[1], reverse=True)[:10]

        return {
            "total_users": len(users),
            "total_updates": len(updates),
            "top_contributors": [{"user": user, "updates": count} for user, count in top],
        }

    def ensure_default_admin(self, default_email: str) -> None:
        email = (default_email or "").strip().lower()
        if not email:
            return
        users = self.get_allowed_users()
        if not users:
            self.upsert_allowed_user(email=email, role="admin", active=True, added_by="System")

    def get_allowed_users(self) -> List[Dict[str, Any]]:
        def _load_rows():
            ws = self._worksheet("allowed_users")
            return self._retry_google_call(ws.get_all_records)

        rows = self._cached_read("allowed_users_records", _load_rows)
        users: List[Dict[str, Any]] = []
        for row in rows:
            email = str(row.get("email", "")).strip().lower()
            if not email:
                continue
            users.append(
                {
                    "email": email,
                    "first_name": str(row.get("first_name", "") or "").strip() or email.split("@", 1)[0].split(".", 1)[0].replace("_", " ").replace("-", " ").title(),
                    "role": str(row.get("role", "viewer") or "viewer").strip().lower(),
                    "active": str(row.get("active", "true")).strip().lower() in {"1", "true", "yes", "on"},
                    "acknowledged_summary": str(row.get("acknowledged_summary", "false")).strip().lower() in {"1", "true", "yes", "on"},
                    "added_by": row.get("added_by", ""),
                    "added_at": row.get("added_at", ""),
                }
            )
        users.sort(key=lambda u: u["email"])
        return users

    def get_allowed_user(self, email: str) -> Dict[str, Any] | None:
        lookup = (email or "").strip().lower()
        if not lookup:
            return None
        for user in self.get_allowed_users():
            if user.get("email", "").lower() == lookup:
                return user
        return None

    def upsert_allowed_user(
        self,
        email: str,
        role: str,
        active: bool,
        added_by: str = "System",
        first_name: str = "",
        acknowledged_summary: Optional[bool] = None,
    ) -> None:
        normalized = (email or "").strip().lower()
        if not normalized:
            raise ValueError("Email is required")

        role_clean = (role or "viewer").strip().lower()
        if role_clean not in {"admin", "editor", "viewer"}:
            role_clean = "viewer"

        ws = self._worksheet("allowed_users")
        header = self._ensure_sheet_columns(
            "allowed_users",
            ["email", "first_name", "role", "active", "acknowledged_summary", "added_by", "added_at"],
        )
        ids = self._retry_google_call(ws.col_values, 1)
        value_active = "true" if active else "false"
        now = _now_iso()
        current_user = self.get_allowed_user(normalized)
        effective_ack = current_user.get("acknowledged_summary", False) if current_user else False
        if acknowledged_summary is not None:
            effective_ack = bool(acknowledged_summary)

        existing_idx = None
        for i, existing_email in enumerate(ids[1:], start=2):
            if str(existing_email).strip().lower() == normalized:
                existing_idx = i
                break

        if existing_idx:
            self._retry_google_call(ws.update_cell, existing_idx, header.index("first_name") + 1, (first_name or "").strip())
            self._retry_google_call(ws.update_cell, existing_idx, header.index("role") + 1, role_clean)
            self._retry_google_call(ws.update_cell, existing_idx, header.index("active") + 1, value_active)
            self._retry_google_call(
                ws.update_cell,
                existing_idx,
                header.index("acknowledged_summary") + 1,
                "true" if effective_ack else "false",
            )
            self._retry_google_call(ws.update_cell, existing_idx, header.index("added_by") + 1, added_by or "System")
            self._retry_google_call(ws.update_cell, existing_idx, header.index("added_at") + 1, now)
        else:
            self._retry_google_call(
                ws.append_row,
                [
                    normalized,
                    (first_name or "").strip(),
                    role_clean,
                    value_active,
                    "true" if effective_ack else "false",
                    added_by or "System",
                    now,
                ],
            )

        self._invalidate_read_cache()

    def set_allowed_user_active(self, email: str, active: bool) -> None:
        user = self.get_allowed_user(email)
        if not user:
            return
        self.upsert_allowed_user(
            email=user["email"],
            role=user.get("role", "viewer"),
            active=active,
            added_by="System",
            first_name=user.get("first_name", ""),
            acknowledged_summary=user.get("acknowledged_summary", False),
        )

    def set_allowed_user_acknowledged(self, email: str, acknowledged: bool = True) -> None:
        user = self.get_allowed_user(email)
        if not user:
            return
        self.upsert_allowed_user(
            email=user["email"],
            role=user.get("role", "viewer"),
            active=user.get("active", True),
            added_by=user.get("added_by", "System") or "System",
            first_name=user.get("first_name", ""),
            acknowledged_summary=acknowledged,
        )


def _read_google_config() -> Dict[str, Any]:
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    service_account_info: Dict[str, Any] = {}

    if service_account_json:
        try:
            service_account_info = json.loads(service_account_json)
        except json.JSONDecodeError:
            service_account_info = {}

    # Streamlit Cloud secrets support
    try:
        import streamlit as st

        if not sheet_id:
            sheet_id = st.secrets.get("GOOGLE_SHEET_ID", "")
        if not service_account_info:
            maybe_sa = st.secrets.get("gcp_service_account", None)
            if isinstance(maybe_sa, dict):
                service_account_info = dict(maybe_sa)
    except Exception:
        pass

    # Local fallback for script execution (e.g., preflight) where st.secrets may be unavailable.
    if not sheet_id or not service_account_info:
        try:
            secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
            if secrets_path.exists():
                with secrets_path.open("rb") as f:
                    secrets_data = tomllib.load(f)
                if not sheet_id:
                    sheet_id = str(secrets_data.get("GOOGLE_SHEET_ID", "")).strip()
                if not service_account_info:
                    maybe_sa = secrets_data.get("gcp_service_account", {})
                    if isinstance(maybe_sa, dict):
                        service_account_info = maybe_sa
        except Exception:
            pass

    return {"sheet_id": sheet_id, "service_account_info": service_account_info}


def _should_use_google() -> bool:
    value = os.getenv("USE_GOOGLE_SHEETS", "").strip().lower()
    if value:
        return value in {"1", "true", "yes", "on"}

    # Check Streamlit secrets
    try:
        import streamlit as st
        secrets_value = st.secrets.get("USE_GOOGLE_SHEETS", "")
        if secrets_value:
            return str(secrets_value).strip().lower() in {"1", "true", "yes", "on"}
    except Exception:
        pass

    # Local fallback for script runs
    try:
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            with secrets_path.open("rb") as f:
                secrets_data = tomllib.load(f)
            secrets_value = str(secrets_data.get("USE_GOOGLE_SHEETS", "")).strip().lower()
            if secrets_value:
                return secrets_value in {"1", "true", "yes", "on"}
    except Exception:
        pass

    return False


def _gspread_available() -> bool:
    try:
        importlib.import_module("gspread")
        return True
    except Exception:
        return False


_backend = None
_backend_reason = ""


def _get_backend():
    global _backend
    global _backend_reason

    if _backend is not None:
        return _backend

    if _should_use_google() and _gspread_available():
        config = _read_google_config()
        if config["sheet_id"] and config["service_account_info"]:
            try:
                _backend = GoogleSheetsBackend(config["sheet_id"], config["service_account_info"])
                _backend_reason = "Google Sheets configured"
                return _backend
            except Exception as exc:
                _backend_reason = f"Google Sheets unavailable, fallback to SQLite ({exc})"
        else:
            _backend_reason = "Google Sheets requested but credentials/sheet ID missing; fallback to SQLite"
    elif _should_use_google() and not _gspread_available():
        _backend_reason = "gspread not installed; fallback to SQLite"
    else:
        _backend_reason = "Using local SQLite backend"

    _backend = SQLiteBackend()
    return _backend


def get_backend_name() -> str:
    return _get_backend().name


def get_backend_status() -> str:
    _get_backend()
    return _backend_reason


def get_backend_health() -> Dict[str, Any]:
    config = _read_google_config()
    use_google_requested = _should_use_google()
    gspread_available = _gspread_available()
    has_sheet_id = bool(config.get("sheet_id"))
    has_service_account = bool(config.get("service_account_info"))

    _get_backend()

    checks: List[Dict[str, Any]] = [
        {
            "check": "Google mode requested",
            "ok": use_google_requested,
            "details": "Set USE_GOOGLE_SHEETS=true to enable Google Sheets mode.",
        },
        {
            "check": "gspread installed",
            "ok": gspread_available,
            "details": "Install gspread and google-auth dependencies.",
        },
        {
            "check": "Google Sheet ID configured",
            "ok": has_sheet_id,
            "details": "Set GOOGLE_SHEET_ID in env vars or Streamlit secrets.",
        },
        {
            "check": "Service account configured",
            "ok": has_service_account,
            "details": "Set gcp_service_account in Streamlit secrets or GOOGLE_SERVICE_ACCOUNT_JSON.",
        },
    ]

    return {
        "backend_name": get_backend_name(),
        "backend_status": get_backend_status(),
        "use_google_requested": use_google_requested,
        "gspread_available": gspread_available,
        "has_sheet_id": has_sheet_id,
        "has_service_account": has_service_account,
        "checks": checks,
    }


def run_connectivity_test() -> Dict[str, Any]:
    try:
        backend = _get_backend()
        tasks = backend.get_all_tasks()
        return {
            "ok": True,
            "backend": backend.name,
            "message": f"Connected successfully. Retrieved {len(tasks)} task records.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "backend": "Unknown",
            "message": str(exc),
        }


def init_db() -> None:
    _get_backend().init_db()


def load_initial_data_from_json() -> None:
    _get_backend().load_initial_data_from_json()


def get_all_phases() -> List[Dict[str, Any]]:
    return _get_backend().get_all_phases()


def get_all_tasks() -> List[Dict[str, Any]]:
    return _get_backend().get_all_tasks()


def get_milestones() -> List[Dict[str, Any]]:
    return _get_backend().get_milestones()


def update_task(task_id: str, status: str, percent_complete: int, notes: str, user_name: str = "Unknown") -> None:
    _get_backend().update_task(task_id, status, percent_complete, notes, user_name)


def update_task_owner(task_id: str, owner: str, user_name: str = "Unknown") -> None:
    backend = _get_backend()
    if hasattr(backend, "update_task_owner"):
        backend.update_task_owner(task_id, owner, user_name)


def update_tasks_bulk(task_ids: List[str], status: str, percent_complete: int, notes: str, user_name: str = "Unknown", owner: str = "") -> None:
    backend = _get_backend()
    if hasattr(backend, "update_tasks_bulk"):
        backend.update_tasks_bulk(task_ids, status, percent_complete, notes, user_name, owner)


def import_tasks_bulk(rows: List[Dict[str, Any]], user_name: str = "Unknown") -> Dict[str, Any]:
    backend = _get_backend()
    if hasattr(backend, "import_tasks_bulk"):
        return backend.import_tasks_bulk(rows, user_name)
    return {"updated": 0}


def get_task_history(task_id: str) -> List[Dict[str, Any]]:
    return _get_backend().get_task_history(task_id)


def get_activity_log(limit: int = 50) -> List[Dict[str, Any]]:
    return _get_backend().get_activity_log(limit)


def get_activity_by_user(user_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    return _get_backend().get_activity_by_user(user_name, limit)


def export_to_json() -> Dict[str, Any]:
    return _get_backend().export_to_json()


def get_team_stats() -> Dict[str, Any]:
    return _get_backend().get_team_stats()


def ensure_default_admin(default_email: str) -> None:
    backend = _get_backend()
    if hasattr(backend, "ensure_default_admin"):
        backend.ensure_default_admin(default_email)


def get_allowed_users() -> List[Dict[str, Any]]:
    backend = _get_backend()
    if hasattr(backend, "get_allowed_users"):
        return backend.get_allowed_users()
    return []


def get_allowed_user(email: str) -> Dict[str, Any] | None:
    backend = _get_backend()
    if hasattr(backend, "get_allowed_user"):
        return backend.get_allowed_user(email)
    return None


def upsert_allowed_user(
    email: str,
    role: str,
    active: bool,
    added_by: str = "System",
    first_name: str = "",
    acknowledged_summary: Optional[bool] = None,
) -> None:
    backend = _get_backend()
    if hasattr(backend, "upsert_allowed_user"):
        backend.upsert_allowed_user(email, role, active, added_by, first_name, acknowledged_summary)


def set_allowed_user_active(email: str, active: bool) -> None:
    backend = _get_backend()
    if hasattr(backend, "set_allowed_user_active"):
        backend.set_allowed_user_active(email, active)


def set_allowed_user_acknowledged(email: str, acknowledged: bool = True) -> None:
    backend = _get_backend()
    if hasattr(backend, "set_allowed_user_acknowledged"):
        backend.set_allowed_user_acknowledged(email, acknowledged)
