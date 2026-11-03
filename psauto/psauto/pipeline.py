"""Create a MaaFramework tasker using a configured resource bundle."""

from maa.resource import Resource
from maa.tasker import Tasker

def create_tasker(resource_dir: str, controller, agent_client=None) -> Tasker:
    resource = Resource()
    if not resource.post_bundle(resource_dir).wait().succeeded:
        raise RuntimeError(f"Failed to load Maa resource bundle: {resource_dir}")
    if agent_client is not None:
        if not agent_client.bind(resource):
            raise RuntimeError("Failed to bind MR3A AgentClient")
        if not agent_client.connect():
            raise RuntimeError("Failed to connect to the original MR3A AgentServer; check psauto/debug/mr3a-agent.log")
    tasker = Tasker()
    if not tasker.bind(resource, controller) or not tasker.inited:
        raise RuntimeError("Failed to initialize Maa tasker")
    return tasker
