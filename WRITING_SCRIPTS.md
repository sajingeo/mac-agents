# Writing Scripts for Mac Agents

## How Mac Agents runs your script

Mac Agents runs your script as a subprocess and captures its **stdout** and **exit code**:

- **Exit code 0** → success (green status, "Completed" notification)
- **Any other exit code** → failure (red status, "Failed" notification)
- **stdout** → shown in the notification body (first 200 chars) and stored in logs
- **stderr** → appended to the output as `[stderr] ...` on failure

The notification title is: `⚡ <Script Name> — Completed` or `⚡ <Script Name> — Failed`

**Timeout:** Scripts are killed after 300 seconds.

---

## The contract: stdout is your message

Whatever you `print()` (or write to stdout) becomes the notification body and the log entry.
Keep your final output short and human-readable — only the first 200 characters appear in the notification.

```python
# Good — clear, concise output
print("Battery at 42% — charging started")

# Bad — walls of debug text will be truncated in the notification
print(json.dumps(huge_response_object))
```

---

## Exit codes

```python
import sys

# Success
sys.exit(0)         # or just let the script end normally

# Failure
sys.exit(1)         # triggers "Failed" notification + red status
```

---

## Python example

```python
#!/usr/bin/env python3
"""Example Mac Agents script."""

import sys

def main():
    try:
        result = do_something()

        if result.needs_attention:
            print(f"Action needed: {result.summary}")
            sys.exit(0)  # still a success — the message is the alert

        print(f"All good: {result.summary}")
        # sys.exit(0) implied

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Shell script example

```bash
#!/bin/bash
set -euo pipefail

VALUE=$(some_command)

if [ "$VALUE" -lt 20 ]; then
    echo "Warning: value is low ($VALUE)"
    exit 0
fi

echo "Value OK: $VALUE"
# exit 0 implied
```

---

## Supported script types

| Extension | Runner         |
|-----------|----------------|
| `.py`     | `python3` (or venv python if configured) |
| `.sh`     | `bash`         |
| `.zsh`    | `zsh`          |
| `.rb`     | `ruby`         |
| `.js`     | `node`         |
| `.ts`     | `npx ts-node`  |

---

## scripts.json entry

When adding manually to `config/scripts.json`:

```json
{
  "id": "<uuid>",
  "name": "My Script",
  "path": "/absolute/path/to/script.py",
  "interval_minutes": 30,
  "enabled": true,
  "venv_path": "/absolute/path/to/.venv"
}
```

- `interval_minutes` — omit or set to `null` for manual-only (run from menubar)
- `venv_path` — omit or set to `null` if no venv needed
- Generate a UUID: `python3 -c "import uuid; print(uuid.uuid4())"`

Restart the service after editing the JSON:
```bash
launchctl unload ~/Library/LaunchAgents/com.macagents.app.plist
launchctl load ~/Library/LaunchAgents/com.macagents.app.plist
```

---

## Tips

- **One responsibility per script** — the notification is a single message, not a dashboard
- **Don't print on success if there's nothing to say** — an empty notification body falls back to "Script finished successfully."
- **Use a venv** if your script has dependencies, so it's isolated from other projects
- **Test your script standalone** before registering it: `python3 /path/to/script.py`
