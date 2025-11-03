try:
    from importlib.metadata import version
    __version__ = version("brainframe-sys-tools")
except Exception:
    __version__ = "unknown"

from .cli import cli_main
from .brainframe_monitor.brainframe_monitor import fps_monitor
from .perf_monitor import perf_monitor
from .bf_info import sys_info
from .bf_service_monitor import service_monitor
from .bf_ssh_tunnel import ssh_tunnel
