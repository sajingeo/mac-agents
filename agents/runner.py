import subprocess
import os
import shlex
from dataclasses import dataclass
from typing import Optional


@dataclass
class RunResult:
    success: bool
    output: str
    exit_code: int


SCRIPT_RUNNERS = {
    ".py": "python3",
    ".sh": "bash",
    ".rb": "ruby",
    ".js": "node",
    ".ts": "npx ts-node",
    ".zsh": "zsh",
}


def _resolve_interpreter(script_path: str, venv_path: Optional[str] = None) -> list[str]:
    ext = os.path.splitext(script_path)[1].lower()

    if ext == ".py" and venv_path:
        venv_python = os.path.join(venv_path, "bin", "python")
        if os.path.isfile(venv_python):
            return [venv_python]

    runner = SCRIPT_RUNNERS.get(ext)
    if runner:
        return shlex.split(runner)

    return []


def run_script(script_path: str, venv_path: Optional[str] = None,
               timeout: int = 300) -> RunResult:
    if not os.path.isfile(script_path):
        return RunResult(success=False, output=f"Script not found: {script_path}", exit_code=-1)

    interpreter = _resolve_interpreter(script_path, venv_path)
    cmd = interpreter + [script_path] if interpreter else [script_path]

    env = os.environ.copy()
    if venv_path:
        env["VIRTUAL_ENV"] = venv_path
        env["PATH"] = os.path.join(venv_path, "bin") + ":" + env.get("PATH", "")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=os.path.dirname(script_path) or None,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr.strip():
            output = f"{output}\n[stderr] {result.stderr.strip()}".strip()
        return RunResult(
            success=result.returncode == 0,
            output=output,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return RunResult(success=False, output=f"Script timed out after {timeout}s", exit_code=-1)
    except Exception as e:
        return RunResult(success=False, output=str(e), exit_code=-1)
