import os
import sys
from pathlib import Path

import data_backend as db


def fail(message: str) -> None:
    print(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"PASS: {message}")


def main() -> int:
    print("Running production preflight for 100-Day Execution Dashboard")

    required_files = [
        Path("streamlit_app.py"),
        Path("data_backend.py"),
        Path("requirements.txt"),
    ]
    for required_file in required_files:
        if required_file.exists():
            ok(f"Found {required_file}")
        else:
            fail(f"Missing required file: {required_file}")
            return 1

    health = db.get_backend_health()
    print(f"Backend detected: {health['backend_name']}")
    print(f"Backend status: {health['backend_status']}")

    # Production policy: Google Sheets must be explicitly requested.
    if not health["use_google_requested"]:
        fail("USE_GOOGLE_SHEETS is not enabled. Set USE_GOOGLE_SHEETS=true for production.")
        return 1
    ok("Google Sheets mode requested")

    for check in health["checks"]:
        if check["ok"]:
            ok(check["check"])
        else:
            fail(f"{check['check']} - {check['details']}")

    # Ensure required sheets/tables exist and baseline data is loaded before connectivity validation.
    db.init_db()
    db.load_initial_data_from_json()

    connectivity = db.run_connectivity_test()
    if not connectivity["ok"]:
        fail(f"Connectivity test failed: {connectivity['message']}")
        return 1
    ok(connectivity["message"])

    if health["backend_name"] != "Google Sheets":
        fail("Active backend is not Google Sheets. Production must not run on SQLite fallback.")
        return 1
    ok("Active backend is Google Sheets")

    print("Preflight complete: READY FOR GO-LIVE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
