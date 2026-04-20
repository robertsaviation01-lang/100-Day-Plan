"""
SQLite database management for 100-Day Execution Plan
Enables team collaboration with user tracking and activity logs
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).with_name("plan_data.db")

def init_db():
    """Initialize database schema on first run"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Tasks table
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phase TEXT NOT NULL,
            start_day INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            status TEXT DEFAULT 'Not Started',
            percent_complete INTEGER DEFAULT 0,
            owner TEXT,
            notes TEXT DEFAULT '',
            predecessors TEXT,
            criticality TEXT DEFAULT 'normal',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Updates/progress log table
    c.execute("""
        CREATE TABLE IF NOT EXISTS task_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            status TEXT,
            percent_complete INTEGER,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    
    # Activity log for audit trail
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            action TEXT NOT NULL,
            task_id TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    
    # Phases table
    c.execute("""
        CREATE TABLE IF NOT EXISTS phases (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            order_num INTEGER
        )
    """)
    
    # Milestones table
    c.execute("""
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day INTEGER NOT NULL,
            name TEXT NOT NULL,
            task_id TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    # Allowed users for lightweight back-office access control
    c.execute("""
        CREATE TABLE IF NOT EXISTS allowed_users (
            email TEXT PRIMARY KEY,
            first_name TEXT,
            role TEXT NOT NULL DEFAULT 'viewer',
            active INTEGER NOT NULL DEFAULT 1,
            acknowledged_summary INTEGER NOT NULL DEFAULT 0,
            added_by TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safe migrations for existing databases.
    c.execute("PRAGMA table_info(tasks)")
    task_columns = {row[1] for row in c.fetchall()}
    if "owner" not in task_columns:
        c.execute("ALTER TABLE tasks ADD COLUMN owner TEXT")
    if "notes" not in task_columns:
        c.execute("ALTER TABLE tasks ADD COLUMN notes TEXT DEFAULT ''")

    c.execute("PRAGMA table_info(allowed_users)")
    allowed_user_columns = {row[1] for row in c.fetchall()}
    if "first_name" not in allowed_user_columns:
        c.execute("ALTER TABLE allowed_users ADD COLUMN first_name TEXT")
    if "acknowledged_summary" not in allowed_user_columns:
        c.execute("ALTER TABLE allowed_users ADD COLUMN acknowledged_summary INTEGER NOT NULL DEFAULT 0")
    
    conn.commit()
    conn.close()

def load_initial_data_from_json():
    """Load initial data from JSON file into database (one-time migration)"""
    json_file = Path(__file__).with_name("plan_data.json")
    
    if not json_file.exists():
        return
    
    # Check if database already has data
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks")
    count = c.fetchone()[0]
    conn.close()
    
    if count > 0:
        return  # Already migrated
    
    # Load and migrate
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Insert phases
    for phase in data.get("phases", []):
        c.execute("""
            INSERT OR IGNORE INTO phases (id, name, order_num)
            VALUES (?, ?, ?)
        """, (phase["id"], phase["name"], phase.get("order", 0)))
    
    # Insert tasks
    for task in data.get("tasks", []):
        c.execute("""
            INSERT OR IGNORE INTO tasks 
            (id, name, phase, start_day, duration, status, percent_complete, owner, notes, predecessors, criticality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task["id"],
            task["name"],
            task["phase"],
            task["startDay"],
            task["duration"],
            task.get("status", "Not Started"),
            task.get("percentComplete", 0),
            task.get("owner", ""),
            task.get("notes", ""),
            json.dumps(task.get("predecessors", [])),
            task.get("criticality", "normal")
        ))
    
    # Insert milestones
    for milestone in data.get("milestones", []):
        c.execute("""
            INSERT INTO milestones (day, name, task_id)
            VALUES (?, ?, ?)
        """, (milestone["day"], milestone["name"], milestone.get("taskId")))
    
    conn.commit()
    conn.close()

def get_all_phases() -> List[Dict[str, Any]]:
    """Get all phases"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, name, order_num FROM phases ORDER BY order_num")
    phases = [dict(row) for row in c.fetchall()]
    conn.close()
    return phases

def get_all_tasks() -> List[Dict[str, Any]]:
    """Get all tasks with parsed predecessors"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, name, phase, start_day, duration, status, percent_complete, owner,
             notes, predecessors, criticality, created_at, updated_at
        FROM tasks
        ORDER BY start_day
    """)
    tasks = []
    for row in c.fetchall():
        task = dict(row)
        task['predecessors'] = json.loads(task.get('predecessors', '[]'))
        task['startDay'] = task.pop('start_day')
        task['percentComplete'] = task.pop('percent_complete')
        tasks.append(task)
    conn.close()
    return tasks

def get_milestones() -> List[Dict[str, Any]]:
    """Get all milestones"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT day, name, task_id FROM milestones ORDER BY day")
    milestones = [dict(row) for row in c.fetchall()]
    conn.close()
    return milestones

def update_task(task_id: str, status: str, percent_complete: int, notes: str, user_name: str = "Unknown"):
    """Update task and log the change"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Update task
    c.execute("""
        UPDATE tasks 
        SET status = ?, percent_complete = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, percent_complete, notes or "", task_id))
    
    # Log update
    c.execute("""
        INSERT INTO task_updates (task_id, user_name, status, percent_complete, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (task_id, user_name, status, percent_complete, notes))
    
    # Log activity
    c.execute("""
        INSERT INTO activity_log (user_name, action, task_id, details)
        VALUES (?, ?, ?, ?)
    """, (
        user_name,
        "Updated task",
        task_id,
        f"Status: {status}, Progress: {percent_complete}%"
    ))
    
    conn.commit()
    conn.close()


def update_task_owner(task_id: str, owner: str, user_name: str = "Unknown"):
    """Update task owner and log the change."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        UPDATE tasks
        SET owner = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (owner, task_id),
    )

    c.execute(
        """
        INSERT INTO activity_log (user_name, action, task_id, details)
        VALUES (?, ?, ?, ?)
        """,
        (user_name, "Updated task owner", task_id, f"Owner: {owner or 'Unassigned'}"),
    )

    conn.commit()
    conn.close()


def update_tasks_bulk(task_ids: List[str], status: str, percent_complete: int, notes: str, user_name: str = "Unknown", owner: str = ""):
    """Bulk update tasks in one transaction to reduce write overhead."""
    if not task_ids:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().isoformat(timespec="seconds")

    for task_id in task_ids:
        c.execute(
            """
            UPDATE tasks
            SET status = ?, percent_complete = ?, owner = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, percent_complete, owner, notes or "", task_id),
        )
        c.execute(
            """
            INSERT INTO task_updates (task_id, user_name, status, percent_complete, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task_id, user_name, status, percent_complete, notes, timestamp),
        )
        c.execute(
            """
            INSERT INTO activity_log (user_name, action, task_id, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_name, "Updated task", task_id, f"Status: {status}, Progress: {percent_complete}%, Owner: {owner or 'Unassigned'}", timestamp),
        )

    conn.commit()
    conn.close()


def import_tasks_bulk(rows: List[Dict[str, Any]], user_name: str = "Unknown") -> Dict[str, Any]:
    """Bulk import revised task rows matched upstream to task ids."""
    if not rows:
        return {"updated": 0}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().isoformat(timespec="seconds")

    updated = 0
    for row in rows:
        task_id = row["task_id"]
        c.execute(
            """
            UPDATE tasks
            SET status = ?,
                percent_complete = ?,
                owner = ?,
                start_day = ?,
                duration = ?,
                criticality = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                row["status"],
                row["percent_complete"],
                row["owner"],
                row["start_day"],
                row["duration"],
                row["criticality"],
                task_id,
            ),
        )
        c.execute(
            """
            INSERT INTO task_updates (task_id, user_name, status, percent_complete, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task_id, user_name, row["status"], row["percent_complete"], "Imported from CSV", timestamp),
        )
        c.execute(
            """
            INSERT INTO activity_log (user_name, action, task_id, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_name,
                "Imported task from CSV",
                task_id,
                f"Status: {row['status']}, Progress: {row['percent_complete']}%, Owner: {row['owner'] or 'Unassigned'}",
                timestamp,
            ),
        )
        updated += 1

    conn.commit()
    conn.close()
    return {"updated": updated}

def get_task_history(task_id: str) -> List[Dict[str, Any]]:
    """Get update history for a specific task"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT user_name, status, percent_complete, notes, updated_at
        FROM task_updates
        WHERE task_id = ?
        ORDER BY updated_at DESC
        LIMIT 20
    """, (task_id,))
    history = [dict(row) for row in c.fetchall()]
    conn.close()
    return history

def get_activity_log(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent activity log for all users"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT user_name, action, task_id, details, created_at
        FROM activity_log
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    log = [dict(row) for row in c.fetchall()]
    conn.close()
    return log

def get_activity_by_user(user_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get activity for a specific user"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT action, task_id, details, created_at
        FROM activity_log
        WHERE user_name = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_name, limit))
    log = [dict(row) for row in c.fetchall()]
    conn.close()
    return log

def export_to_json() -> Dict[str, Any]:
    """Export all data to JSON format for backup"""
    return {
        "phases": get_all_phases(),
        "tasks": get_all_tasks(),
        "milestones": get_milestones(),
        "exported_at": datetime.now().isoformat()
    }

def get_team_stats() -> Dict[str, Any]:
    """Get team collaboration statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Count unique users
    c.execute("SELECT COUNT(DISTINCT user_name) FROM activity_log")
    total_users = c.fetchone()[0]
    
    # Count total updates
    c.execute("SELECT COUNT(*) FROM task_updates")
    total_updates = c.fetchone()[0]
    
    # Get top contributors
    c.execute("""
        SELECT user_name, COUNT(*) as update_count
        FROM activity_log
        WHERE action = 'Updated task'
        GROUP BY user_name
        ORDER BY update_count DESC
        LIMIT 10
    """)
    top_contributors = [{"user": row[0], "updates": row[1]} for row in c.fetchall()]
    
    conn.close()
    
    return {
        "total_users": total_users,
        "total_updates": total_updates,
        "top_contributors": top_contributors
    }


def ensure_default_admin(default_email: Optional[str]) -> None:
    """Bootstrap one admin if allowlist is empty and default email is provided."""
    if not default_email:
        return

    email = default_email.strip().lower()
    if not email:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM allowed_users")
    count = c.fetchone()[0]
    if count == 0:
        c.execute(
            """
            INSERT OR REPLACE INTO allowed_users (email, role, active, added_by)
            VALUES (?, 'admin', 1, 'System')
            """,
            (email,),
        )
    conn.commit()
    conn.close()


def get_allowed_users() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """
        SELECT email, first_name, role, active, acknowledged_summary, added_by, added_at
        FROM allowed_users
        ORDER BY email COLLATE NOCASE
        """
    )
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    for row in rows:
        row["active"] = bool(row.get("active", 0))
        row["acknowledged_summary"] = bool(row.get("acknowledged_summary", 0))
        if not row.get("first_name"):
            local_part = row.get("email", "").split("@", 1)[0]
            row["first_name"] = local_part.split(".", 1)[0].replace("_", " ").replace("-", " ").title()
    return rows


def get_allowed_user(email: str) -> Optional[Dict[str, Any]]:
    lookup = (email or "").strip().lower()
    if not lookup:
        return None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """
        SELECT email, first_name, role, active, acknowledged_summary, added_by, added_at
        FROM allowed_users
        WHERE lower(email) = ?
        LIMIT 1
        """,
        (lookup,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    item["active"] = bool(item.get("active", 0))
    item["acknowledged_summary"] = bool(item.get("acknowledged_summary", 0))
    if not item.get("first_name"):
        local_part = item.get("email", "").split("@", 1)[0]
        item["first_name"] = local_part.split(".", 1)[0].replace("_", " ").replace("-", " ").title()
    return item


def upsert_allowed_user(
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

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    existing_ack = 0
    c.execute("SELECT acknowledged_summary FROM allowed_users WHERE lower(email) = ? LIMIT 1", (normalized,))
    existing_row = c.fetchone()
    if existing_row is not None:
        existing_ack = int(existing_row[0] or 0)

    effective_ack = existing_ack if acknowledged_summary is None else (1 if acknowledged_summary else 0)
    c.execute(
        """
        INSERT OR REPLACE INTO allowed_users (email, first_name, role, active, acknowledged_summary, added_by, added_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            normalized,
            (first_name or "").strip(),
            role_clean,
            1 if active else 0,
            effective_ack,
            added_by or "System",
        ),
    )
    conn.commit()
    conn.close()


def set_allowed_user_acknowledged(email: str, acknowledged: bool = True) -> None:
    normalized = (email or "").strip().lower()
    if not normalized:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE allowed_users SET acknowledged_summary = ? WHERE lower(email) = ?",
        (1 if acknowledged else 0, normalized),
    )
    conn.commit()
    conn.close()


def set_allowed_user_active(email: str, active: bool) -> None:
    normalized = (email or "").strip().lower()
    if not normalized:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE allowed_users SET active = ? WHERE lower(email) = ?",
        (1 if active else 0, normalized),
    )
    conn.commit()
    conn.close()
