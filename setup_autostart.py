#!/usr/bin/env python3
"""Install or uninstall MAC Agents as a macOS Launch Agent (auto-start on login)."""

import os
import sys
import plistlib
import subprocess

APP_LABEL = "com.macagents.app"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{APP_LABEL}.plist")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
MAIN_SCRIPT = os.path.join(PROJECT_DIR, "main.py")
LOG_DIR = os.path.join(PROJECT_DIR, "config", "logs")


def install():
    if not os.path.isfile(VENV_PYTHON):
        print(f"Error: venv python not found at {VENV_PYTHON}")
        print("Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt")
        sys.exit(1)

    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(PLIST_PATH), exist_ok=True)

    plist = {
        "Label": APP_LABEL,
        "ProgramArguments": [VENV_PYTHON, MAIN_SCRIPT],
        "RunAtLoad": True,
        "WorkingDirectory": PROJECT_DIR,
        "StandardOutPath": os.path.join(LOG_DIR, "launchd_stdout.log"),
        "StandardErrorPath": os.path.join(LOG_DIR, "launchd_stderr.log"),
        "KeepAlive": {"SuccessfulExit": False},
        "EnvironmentVariables": {
            "PATH": "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin",
        },
    }

    with open(PLIST_PATH, "wb") as f:
        plistlib.dump(plist, f)

    subprocess.run(["launchctl", "unload", PLIST_PATH], capture_output=True)
    result = subprocess.run(["launchctl", "load", PLIST_PATH], capture_output=True, text=True)

    if result.returncode == 0:
        print("MAC Agents installed as a Launch Agent.")
        print(f"  Plist: {PLIST_PATH}")
        print(f"  Logs:  {LOG_DIR}/launchd_*.log")
        print()
        print("It will now start automatically on login.")
        print("To start it right now without rebooting, it should already be running.")
        print("To uninstall: python3 setup_autostart.py uninstall")
    else:
        print(f"Failed to load Launch Agent: {result.stderr}")
        sys.exit(1)


def uninstall():
    if not os.path.exists(PLIST_PATH):
        print("Launch Agent is not installed.")
        return

    subprocess.run(["launchctl", "unload", PLIST_PATH], capture_output=True)
    os.remove(PLIST_PATH)
    print("MAC Agents Launch Agent uninstalled.")
    print("The app will no longer start on login.")


def status():
    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        if APP_LABEL in line:
            print(f"Running: {line}")
            return
    print("MAC Agents is not currently loaded as a Launch Agent.")
    if os.path.exists(PLIST_PATH):
        print(f"  (plist exists at {PLIST_PATH} but agent is not loaded)")


if __name__ == "__main__":
    commands = {"install": install, "uninstall": uninstall, "status": status}
    cmd = sys.argv[1] if len(sys.argv) > 1 else None

    if cmd not in commands:
        print("Usage: python3 setup_autostart.py [install|uninstall|status]")
        print()
        print("  install    — register MAC Agents to start on login")
        print("  uninstall  — remove auto-start")
        print("  status     — check if the Launch Agent is running")
        sys.exit(1)

    commands[cmd]()
