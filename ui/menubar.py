import rumps
import threading
from datetime import datetime

from agents.manager import ScriptManager
from agents.scheduler import AgentScheduler
from ui.add_script import prompt_add_script


class MacAgentsApp(rumps.App):
    def __init__(self, manager: ScriptManager, scheduler: AgentScheduler):
        super().__init__("⚡", quit_button=None)
        self._manager = manager
        self._scheduler = scheduler
        self._build_menu()

        self._refresh_timer = rumps.Timer(self._on_tick, 5)
        self._refresh_timer.start()

    def _build_menu(self):
        self.menu.clear()
        scripts = self._manager.all()

        if not scripts:
            self.menu.add(rumps.MenuItem("No scripts configured", callback=None))
        else:
            scheduled = [s for s in scripts if not s.is_manual]
            manual = [s for s in scripts if s.is_manual]

            if scheduled:
                self.menu.add(rumps.MenuItem("— Scheduled —", callback=None))
                for script in scheduled:
                    self.menu.add(self._build_script_submenu(script))

            if manual:
                if scheduled:
                    self.menu.add(rumps.separator)
                self.menu.add(rumps.MenuItem("— Manual —", callback=None))
                for script in manual:
                    self.menu.add(self._build_script_submenu(script))

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Add Script...", callback=self._on_add_script))
        self.menu.add(rumps.MenuItem("Refresh", callback=lambda _: self._build_menu()))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit", callback=self._on_quit))

    def _build_script_submenu(self, script):
        status_icon = "✅" if script.last_status == "success" else ("❌" if script.last_status == "fail" else "⏳")

        if script.is_manual:
            title = f"{status_icon}  {script.name}  —  manual"
        else:
            next_run = self._scheduler.get_next_run(script.id)
            countdown = self._format_countdown(next_run)
            title = f"{status_icon}  {script.name}  —  {countdown}"

        item = rumps.MenuItem(title)

        if script.last_output:
            display_output = script.last_output[:120]
            item.add(rumps.MenuItem(f"Output: {display_output}", callback=None))

        if script.last_run:
            try:
                dt = datetime.fromisoformat(script.last_run)
                item.add(rumps.MenuItem(f"Last run: {dt.strftime('%H:%M:%S')}", callback=None))
            except ValueError:
                pass

        if script.is_manual:
            item.add(rumps.MenuItem("Trigger: manual only", callback=None))
        else:
            item.add(rumps.MenuItem(f"Interval: {script.interval_minutes} min", callback=None))

        enabled_label = "enabled" if script.enabled else "disabled"
        item.add(rumps.MenuItem(f"Status: {enabled_label}", callback=None))
        item.add(rumps.separator)

        run_item = rumps.MenuItem("Run Now", callback=lambda _, sid=script.id: self._on_run_now(sid))
        item.add(run_item)

        logs_item = rumps.MenuItem("View Logs", callback=lambda _, sid=script.id, sname=script.name: self._on_view_logs(sid, sname))
        item.add(logs_item)

        if not script.is_manual:
            toggle_label = "Disable" if script.enabled else "Enable"
            toggle_item = rumps.MenuItem(toggle_label, callback=lambda _, sid=script.id, en=script.enabled: self._on_toggle(sid, en))
            item.add(toggle_item)

        remove_item = rumps.MenuItem("Remove", callback=lambda _, sid=script.id: self._on_remove(sid))
        item.add(remove_item)

        return item

    def _format_countdown(self, next_run: datetime | None) -> str:
        if not next_run:
            return "not scheduled"
        diff = next_run - datetime.now()
        total_seconds = int(diff.total_seconds())
        if total_seconds <= 0:
            return "running soon"
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"next in {hours}h {minutes}m"
        if minutes > 0:
            return f"next in {minutes}m {seconds}s"
        return f"next in {seconds}s"

    def _on_tick(self, _):
        self._build_menu()

    def _on_add_script(self, _):
        result = prompt_add_script()
        if result:
            script = self._manager.add(**result)
            if script.enabled and not script.is_manual:
                self._scheduler.schedule(script)
            self._build_menu()

    def _on_run_now(self, script_id):
        def _do():
            self._scheduler.run_now(script_id)
            self._build_menu()
        threading.Thread(target=_do, daemon=True).start()

    def _on_view_logs(self, script_id, script_name):
        logs = self._manager.get_logs(script_id, limit=10)
        if not logs:
            rumps.alert(f"Logs — {script_name}", "No runs recorded yet.")
            return
        lines = []
        for entry in reversed(logs):
            try:
                dt = datetime.fromisoformat(entry.timestamp)
                ts = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                ts = entry.timestamp
            icon = "✅" if entry.status == "success" else "❌"
            output_preview = entry.output[:80].replace("\n", " ") if entry.output else ""
            lines.append(f"{icon} {ts}  (exit {entry.exit_code})")
            if output_preview:
                lines.append(f"   {output_preview}")
        body = "\n".join(lines)
        rumps.alert(f"Logs — {script_name} (last {len(logs)})", body)

    def _on_toggle(self, script_id, currently_enabled):
        self._manager.update(script_id, enabled=not currently_enabled)
        script = self._manager.get(script_id)
        if script and script.enabled and not script.is_manual:
            self._scheduler.schedule(script)
        else:
            self._scheduler.unschedule(script_id)
        self._build_menu()

    def _on_remove(self, script_id):
        self._scheduler.unschedule(script_id)
        self._manager.remove(script_id)
        self._build_menu()

    def _on_quit(self, _):
        self._scheduler.stop()
        rumps.quit_application()
