"""Create a MaaFramework tasker using a configured resource bundle."""

from maa.resource import Resource
from maa.tasker import Tasker

from .actions import Hotkey


def create_tasker(resource_dir: str, controller) -> Tasker:
    resource = Resource()
    if not resource.post_bundle(resource_dir).wait().succeeded:
        raise RuntimeError(f"Failed to load Maa resource bundle: {resource_dir}")
    if not resource.register_custom_action("Hotkey", Hotkey(controller)):
        raise RuntimeError("Failed to register Hotkey action")
    tasker = Tasker()
    if not tasker.bind(resource, controller) or not tasker.inited:
        raise RuntimeError("Failed to initialize Maa tasker")
    return tasker
