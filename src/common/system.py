import config
import os
import subprocess
from common.errors import logger


def dnsmasq():
    # Build the list of args
    args = [
        "/usr/sbin/dnsmasq",
        f"--address=/#/{config.DEFAULT_GATEWAY}",
        f"--dhcp-range={config.DEFAULT_DHCP_RANGE}",
        f"--dhcp-option=option:router,{config.DEFAULT_GATEWAY}",
        f"--interface={config.interface}",
        "--keep-in-foreground",
        "--bind-dynamic",
        "--except-interface=lo",
        "--conf-file",
        "--no-hosts",
    ]

    try:
        subprocess.Popen(args)
    except Exception:
        logger.exception("Failed to start dnsmasq.")


def led(mode):
    # Activate LED on compatible devices
    # 1 = on
    # 0 = off
    if "PWC_LED" not in os.environ or (
        "PWC_LED" in os.environ and os.environ["PWC_LED"].lower() == "on"
    ):
        try:
            with open("/sys/class/leds/led0/brightness", "w+") as f:
                f.write(str(mode))
        except Exception:
            # This is not possible on some devices.
            pass
