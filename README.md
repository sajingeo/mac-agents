# MAC Agents

A macOS menu bar app that lets you schedule and manage scripts. It shows live countdowns, sends native notifications on completion, displays script output, and supports Python virtual environments.

## Features

- **Menu bar icon** with live status and countdown to next run
- **Native macOS notifications** when scripts run (success/fail)
- **Script output display** — see returned data (weather, battery %, etc.)
- **Simple UI** to add, edit, and remove scripts
- **Python venv support** — run scripts inside a virtual environment
- **Manual scripts** — add scripts with no interval, trigger them from the menu bar
- **Run logs** — persistent per-script log history with timestamps, exit codes, and output

## Installation

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

A menu bar icon (⚡) will appear in your macOS status bar. Click it to see scheduled scripts, their status, and countdowns. Use "Add Script..." to schedule a new script.

## Adding Scripts

Each script needs:

- **Name** — a display label
- **Path** — absolute path to the script file
- **Interval** — how often to run, in minutes (leave blank for manual trigger only)
- **Venv** (optional) — path to a Python virtual environment to use

## Start on Login

To have MAC Agents launch automatically when you log in:

```bash
python3 setup_autostart.py install
```

This creates a macOS Launch Agent at `~/Library/LaunchAgents/com.macagents.app.plist`.

Other commands:

```bash
python3 setup_autostart.py status      # check if it's running
python3 setup_autostart.py uninstall   # remove auto-start
```

## Configuration

Scripts are persisted in `config/scripts.json`. You can edit this file directly or use the UI.
