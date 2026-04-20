"""Google Drive Dataroom integration for the AceHawk 100-Day Plan dashboard."""

from __future__ import annotations

from typing import Any

# ── Folder IDs ──────────────────────────────────────────────────────────────
# Root dataroom folder
DATAROOM_ROOT_ID = "1StXDq1rhLnqqIGq-_lY42OJSB7iz74Es"

# Execution Plan: folders linked to the overall plan overview
EXECUTION_PLAN_FOLDERS: list[tuple[str, str]] = [
    ("Executive Summary", "1n0yqRI8PqNWxRXTfPycwScduAGvOsRQp"),
    ("Critical Path & 100-Day Plan", "1WJxpTTBfguGP7obLGxjrGl3pIb4mJ6S1"),
]

# Per-workstream folder mapping: ws_id → list of (section_label, folder_id)
WORKSTREAM_DATAROOM_FOLDERS: dict[str, list[tuple[str, str]]] = {
    "ws1": [
        ("1.1 Group Structure", "1zNeJWvBf1iJgnYVQqnxX1s9TUdQcIhgx"),
        ("1.3 Governance", "1BGvMK_rV11ZjPB8YC1bPg186k_l-wgb2"),
        ("1.4 Registers", "13MxMxXpJRkrfrz-B0wbve3SBWYb-jk2A"),
    ],
    "ws2": [
        ("UK OpCo – Incorporation", "1APQEQBIBg1ekcveOQau4VA3180JoLzWG"),
        ("Ireland SPV – Incorporation", "1LY929uhcBIILjuLHFk_hYYFUdmWxSTr_"),
        ("US OpCo – Incorporation", "1BNvsblFEXeac52fd8GkR6CQJKrRdRX2W"),
        ("US HoldCo – Incorporation", "1mNyCzDwtoH3m4ra1uQ__8oAbCjxH7cqJ"),
    ],
    "ws3": [
        ("2.2 Intercompany Agreements", "1thyxhc0xoGg2f7C541u9tOWNf7q1AzUf"),
        ("2.3 IP & Licensing", "192JIPgJlxVzEfe3ard16D9CFcxei52T6"),
        ("3. Financials", "1HLASIzqtU_C4ZpuwYaoD4jlfv_nUCbS_"),
    ],
    "ws4": [
        ("9. Risk & Compliance", "1O8dsaLqbvOQE-Bl2Agglwe9som87E0rT"),
        ("2.4 Insurance", "1nINTyz98VUv1gbEbIeJTk6wid12XfPjn"),
        ("2.1 Constitutional Docs", "1CC3B5aT_UGgX5fiHQmutEsoPMPN1C7ds"),
    ],
    "ws5": [
        ("0. Executive Summary", "1n0yqRI8PqNWxRXTfPycwScduAGvOsRQp"),
        ("4. Investment Materials", "16Z061efpp3k96eBDX2aLoJdO4hNfQgHp"),
        ("1.3 Governance", "1BGvMK_rV11ZjPB8YC1bPg186k_l-wgb2"),
    ],
    "ws6": [
        ("5. Operations", "1m6HF2shPwyFIsQ5_DkAmIMgy1HkbfcfG"),
        ("6. Demonstrator Aircraft", "1omZvOhAQTY3p9tscd1AMBd5uWwfYIKCI"),
        ("7. BEST Auction Strategy", "1Xrf5b95bRX92e1NQoBxUTyH5SMh3dkpr"),
        ("8. Market & Commercial", "1cDrRoyRV0JW4X8kfARP4WjBhNbjLJnHP"),
        ("10. People", "1Ufj4xs0mXbfzfIBN4Tdev_UR0bFFLYNO"),
    ],
}

FOLDER_MIME = "application/vnd.google-apps.folder"


def get_drive_service(sa_info: dict) -> Any:
    """Build and return an authenticated Google Drive v3 service client."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_info(
        sa_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)


def list_folder_files(drive_service: Any, folder_id: str) -> list[dict]:
    """Return direct file children of a folder (excludes sub-folders)."""
    result = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType != '{FOLDER_MIME}'",
        fields="files(id,name,mimeType,webViewLink)",
        pageSize=50,
        orderBy="name",
    ).execute()
    return result.get("files", [])
