import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from agents.manager import ScriptManager, ScriptConfig
from agents.runner import run_script
from agents.notifier import notify_run_result

log = logging.getLogger(__name__)


class AgentScheduler:
    def __init__(self, manager: ScriptManager):
        self._manager = manager
        self._scheduler = BackgroundScheduler(daemon=True)
        self._job_ids: dict[str, str] = {}

    def start(self):
        self._scheduler.start()
        for script in self._manager.all():
            if script.enabled and not script.is_manual:
                self.schedule(script)

    def stop(self):
        self._scheduler.shutdown(wait=False)

    def schedule(self, script: ScriptConfig):
        if script.is_manual:
            return
        if script.id in self._job_ids:
            self.unschedule(script.id)

        job = self._scheduler.add_job(
            self._run,
            trigger=IntervalTrigger(minutes=script.interval_minutes),
            args=[script.id],
            id=f"script-{script.id}",
            next_run_time=datetime.now() + timedelta(minutes=script.interval_minutes),
            replace_existing=True,
        )
        self._job_ids[script.id] = job.id
        log.info("Scheduled %s every %d min", script.name, script.interval_minutes)

    def unschedule(self, script_id: str):
        job_id = self._job_ids.pop(script_id, None)
        if job_id:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass

    def run_now(self, script_id: str):
        self._run(script_id)

    def get_next_run(self, script_id: str) -> datetime | None:
        job_id = self._job_ids.get(script_id)
        if not job_id:
            return None
        job = self._scheduler.get_job(job_id)
        if job and job.next_run_time:
            return job.next_run_time.replace(tzinfo=None)
        return None

    def _run(self, script_id: str):
        script = self._manager.get(script_id)
        if not script or not script.enabled:
            return
        log.info("Running %s (%s)", script.name, script.path)
        result = run_script(script.path, venv_path=script.venv_path)
        self._manager.record_run(script.id, result.success, result.output, result.exit_code)
        if script.notify:
            notify_run_result(script.name, result.success, result.output)
        log.info("Finished %s — %s", script.name, "OK" if result.success else "FAIL")
