import subprocess


def notify(title: str, message: str, sound: bool = True):
    script_parts = [
        f'display notification "{_escape(message)}"',
        f'with title "{_escape(title)}"',
    ]
    if sound:
        script_parts.append('sound name "Funk"')
    applescript = " ".join(script_parts)
    subprocess.Popen(
        ["osascript", "-e", applescript],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def notify_run_result(script_name: str, success: bool, output: str):
    status = "Completed" if success else "Failed"
    title = f"⚡ {script_name} — {status}"
    body = output[:200] if output else ("Script finished successfully." if success else "Script failed. Check logs.")
    notify(title, body)


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
