import config
import subprocess
from common.errors import logger


def dnsmasq():
    # Build the list of args
    args = ["/usr/sbin/dnsmasq",
            f"--address=/#/{config.DEFAULT_GATEWAY}",
            f"--dhcp-range={config.DEFAULT_DHCP_RANGE}",
            f"--dhcp-option=option:router,{config.DEFAULT_GATEWAY}",
            f"--interface={config.DEFAULT_INTERFACE}",
            "--keep-in-foreground",
            "--bind-dynamic",
            "--except-interface=lo",
            "--conf-file",
            "--no-hosts"]

    try:
        subprocess.Popen(args)
    except Exception:
        logger.exception('Failed to start dnsmasq.')
