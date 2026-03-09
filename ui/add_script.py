import rumps
from typing import Optional


def prompt_add_script() -> Optional[dict]:
    name_window = rumps.Window(
        message="Enter a display name for this script:",
        title="Add Script — Name",
        default_text="",
        ok="Next",
        cancel="Cancel",
        dimensions=(320, 24),
    )
    name_resp = name_window.run()
    if not name_resp.clicked or not name_resp.text.strip():
        return None
    name = name_resp.text.strip()

    path_window = rumps.Window(
        message="Full path to the script file:",
        title="Add Script — Path",
        default_text="",
        ok="Next",
        cancel="Cancel",
        dimensions=(420, 24),
    )
    path_resp = path_window.run()
    if not path_resp.clicked or not path_resp.text.strip():
        return None
    path = path_resp.text.strip()

    interval_window = rumps.Window(
        message="Run every N minutes (leave blank for manual trigger only):",
        title="Add Script — Interval",
        default_text="",
        ok="Next",
        cancel="Cancel",
        dimensions=(200, 24),
    )
    interval_resp = interval_window.run()
    if not interval_resp.clicked:
        return None
    interval_text = interval_resp.text.strip()
    if interval_text:
        try:
            interval = int(interval_text)
            if interval < 1:
                raise ValueError
        except ValueError:
            rumps.alert("Invalid interval", "Please enter a positive integer for minutes, or leave blank for manual.")
            return None
    else:
        interval = None

    venv_window = rumps.Window(
        message="(Optional) Path to Python venv for this script.\nLeave blank if not needed:",
        title="Add Script — Venv",
        default_text="",
        ok="Add",
        cancel="Cancel",
        dimensions=(420, 24),
    )
    venv_resp = venv_window.run()
    if not venv_resp.clicked:
        return None
    venv_path = venv_resp.text.strip() or None

    return {
        "name": name,
        "path": path,
        "interval_minutes": interval,
        "venv_path": venv_path,
    }
