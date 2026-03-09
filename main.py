import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agents.manager import ScriptManager
from agents.scheduler import AgentScheduler
from ui.menubar import MacAgentsApp


def hide_dock_icon():
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    hide_dock_icon()

    manager = ScriptManager()
    scheduler = AgentScheduler(manager)
    scheduler.start()

    app = MacAgentsApp(manager, scheduler)
    app.run()


if __name__ == "__main__":
    main()
