"""MaaFramework custom actions used by psauto pipelines."""

import json
import logging

from maa.custom_action import CustomAction

log = logging.getLogger(__name__)


class Hotkey(CustomAction):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self, context, argv) -> bool:
        try:
            keys = json.loads(argv.custom_action_param)["keys"]
            if not isinstance(keys, list) or not keys or not all(isinstance(key, str) and key for key in keys):
                raise ValueError("keys must be a non-empty list of Playwright key names")
            return self.controller.press_combo(keys)
        except (ValueError, TypeError, KeyError):
            log.exception("Invalid Hotkey parameters")
            return False
