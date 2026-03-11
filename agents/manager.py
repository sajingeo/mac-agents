import json
import uuid
import os
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
SCRIPTS_FILE = os.path.join(CONFIG_DIR, "scripts.json")
LOGS_DIR = os.path.join(CONFIG_DIR, "logs")

MAX_LOG_ENTRIES = 100


@dataclass
class RunLogEntry:
    timestamp: str
    status: str  # "success" or "fail"
    exit_code: int
    output: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RunLogEntry":
        return cls(**data)


@dataclass
class ScriptConfig:
    name: str
    path: str
    interval_minutes: Optional[int] = None
    enabled: bool = True
    venv_path: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notify: bool = False
    last_run: Optional[str] = None
    last_status: Optional[str] = None  # "success", "fail", or None
    last_output: Optional[str] = None

    @property
    def is_manual(self) -> bool:
        return self.interval_minutes is None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptConfig":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


class ScriptManager:
    def __init__(self, config_path: str = SCRIPTS_FILE, logs_dir: str = LOGS_DIR):
        self._path = config_path
        self._logs_dir = logs_dir
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        os.makedirs(self._logs_dir, exist_ok=True)
        self._scripts: dict[str, ScriptConfig] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self._path):
            self._scripts = {}
            return
        with open(self._path, "r") as f:
            data = json.load(f)
        self._scripts = {s["id"]: ScriptConfig.from_dict(s) for s in data}

    def _save(self):
        with open(self._path, "w") as f:
            json.dump([s.to_dict() for s in self._scripts.values()], f, indent=2)

    def _log_path(self, script_id: str) -> str:
        return os.path.join(self._logs_dir, f"{script_id}.json")

    def all(self) -> list[ScriptConfig]:
        return list(self._scripts.values())

    def get(self, script_id: str) -> Optional[ScriptConfig]:
        return self._scripts.get(script_id)

    def add(self, name: str, path: str, interval_minutes: Optional[int] = None,
            venv_path: Optional[str] = None) -> ScriptConfig:
        script = ScriptConfig(
            name=name,
            path=path,
            interval_minutes=interval_minutes,
            venv_path=venv_path,
        )
        self._scripts[script.id] = script
        self._save()
        return script

    def update(self, script_id: str, **kwargs) -> Optional[ScriptConfig]:
        script = self._scripts.get(script_id)
        if not script:
            return None
        for key, val in kwargs.items():
            if hasattr(script, key):
                setattr(script, key, val)
        self._save()
        return script

    def remove(self, script_id: str) -> bool:
        if script_id in self._scripts:
            del self._scripts[script_id]
            self._save()
            log_file = self._log_path(script_id)
            if os.path.exists(log_file):
                os.remove(log_file)
            return True
        return False

    def record_run(self, script_id: str, success: bool, output: str, exit_code: int = 0):
        script = self._scripts.get(script_id)
        if not script:
            return
        now = datetime.now().isoformat()
        script.last_run = now
        script.last_status = "success" if success else "fail"
        script.last_output = output[:500] if output else ""
        self._save()

        entry = RunLogEntry(
            timestamp=now,
            status="success" if success else "fail",
            exit_code=exit_code,
            output=output[:2000] if output else "",
        )
        self._append_log(script_id, entry)

    def get_logs(self, script_id: str, limit: int = 20) -> list[RunLogEntry]:
        log_file = self._log_path(script_id)
        if not os.path.exists(log_file):
            return []
        with open(log_file, "r") as f:
            entries = json.load(f)
        return [RunLogEntry.from_dict(e) for e in entries[-limit:]]

    def _append_log(self, script_id: str, entry: RunLogEntry):
        log_file = self._log_path(script_id)
        entries: list[dict] = []
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                entries = json.load(f)
        entries.append(entry.to_dict())
        if len(entries) > MAX_LOG_ENTRIES:
            entries = entries[-MAX_LOG_ENTRIES:]
        with open(log_file, "w") as f:
            json.dump(entries, f, indent=2)
