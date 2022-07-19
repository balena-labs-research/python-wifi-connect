import os
from dotenv import dotenv_values

# Set dev env variables
if (
    "FLASK_ENV" in os.environ
    and os.environ["FLASK_ENV"].lower() == "production"
):
    dev_mode = False
else:
    dev_mode = True

# Check db directory exists
if not os.path.exists("db"):
    os.makedirs("db")

# Import database file
env_file = dotenv_values("db/.db")

# Set default Wi-Fi SSID.
if "PWC_HOTSPOT_SSID" in env_file:
    hotspot_ssid = env_file["PWC_HOTSPOT_SSID"]
elif "PWC_HOTSPOT_SSID" in os.environ:
    hotspot_ssid = os.environ["PWC_HOTSPOT_SSID"]
else:
    hotspot_ssid = "Py Wi-Fi Connect"

# Set default hotspot password.
if "PWC_HOTSPOT_PASSWORD" in env_file:
    hotspot_password = env_file["PWC_HOTSPOT_PASSWORD"]
elif "PWC_HOTSPOT_PASSWORD" in os.environ:
    hotspot_password = os.environ["PWC_HOTSPOT_PASSWORD"]
else:
    hotspot_password = None

# Set default host.
if "PWC_HOST" in os.environ and os.environ["PWC_HOST"].lower() == "bridge":
    host = os.environ["BRIDGE_NETWORK_IP"]
elif "PWC_HOST" in os.environ:
    host = os.environ["PWC_HOST"]
else:
    host = "0.0.0.0"

# Set default port.
if "PWC_PORT" in os.environ:
    port = os.environ["PWC_PORT"]
else:
    port = 9090

# Compile kwargs for automatic connection
if "PWC_AC_SSID" in os.environ:
    auto_connect_kargs = {"ssid": os.environ["PWC_AC_SSID"]}

    if "PWC_AC_USERNAME" in os.environ:
        auto_connect_kargs.update(username=os.environ["PWC_AC_USERNAME"])
    if "PWC_AC_PASSWORD" in os.environ:
        auto_connect_kargs.update(password=os.environ["PWC_AC_PASSWORD"])
else:
    auto_connect_kargs = False

# Default access point name. No need to change these under usual operation as
# they are for use inside the app only. PWC is acronym for 'Py Wi-Fi Connect'.
ap_name = "PWC"

# dnsmasq variables
DEFAULT_GATEWAY = "192.168.42.1"
DEFAULT_DHCP_RANGE = "192.168.42.2,192.168.42.254"

# Wi-Fi modes. No need to rename these, they are used only as labels.
type_hotspot = "HOTSPOT"
type_none = "NONE"
type_wep = "WEP"
type_wpa = "WPA"
type_wpa2 = "WPA2"
type_enterprise = "ENTERPRISE"
