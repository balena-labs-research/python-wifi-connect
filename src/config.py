import os

# Set default Wi-Fi SSID.
if "HOTSPOT_SSID" in os.environ:
    hotspot_ssid = os.environ['HOTSPOT_SSID']
else:
    hotspot_ssid = "Py Wi-Fi Connect"

# Set default hotspot password.
if "HOTSPOT_PASSWORD" in os.environ:
    hotspot_password = os.environ['HOTSPOT_PASSWORD']
else:
    hotspot_password = None

# Default access point name. No need to change these under usual operation as
# they are for use inside the app only. PWC is acronym for 'Py Wi-Fi Connect'.
ap_name = 'PWC'

# dnsmasq variables
DEFAULT_GATEWAY = "192.168.42.1"
DEFAULT_DHCP_RANGE = "192.168.42.2,192.168.42.254"
DEFAULT_INTERFACE = "wlan0"  # use 'ip link show' to see list of interfaces

# Wi-Fi modes. No need to rename these, they are used only as labels.
type_hotspot = 'HOTSPOT'
type_none = 'NONE'
type_wep = 'WEP'
type_wpa = 'WPA'
type_wpa2 = 'WPA2'
type_enterprise = 'ENTERPRISE'

# Set dev env variables
if "FLASK_ENV" in os.environ and \
        os.environ['FLASK_ENV'].lower() == "production":
    dev_mode = False
else:
    dev_mode = True
