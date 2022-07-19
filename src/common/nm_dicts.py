import config
import uuid
from common.errors import logger
from common.errors import WifiInvalidConnectionType


def get_nm_dict(conn_type, ssid, username, password):
    if conn_type == config.type_hotspot:
        # Hotspot for user to connect to device
        hs_dict = {
            "802-11-wireless": {
                "band": "bg",
                "mode": "ap",
                "ssid": config.hotspot_ssid,
            },
            "connection": {
                "autoconnect": False,
                "id": config.ap_name,
                "interface-name": config.interface,
                "type": "802-11-wireless",
                "uuid": str(uuid.uuid4()),
            },
            "ipv4": {
                "address-data": [{"address": "192.168.42.1", "prefix": 24}],
                "addresses": [["192.168.42.1", 24, "0.0.0.0"]],
                "method": "manual",
            },
            "ipv6": {"method": "auto"},
        }

        # Include a key-mgmt string in hotspot if setting a password
        if config.hotspot_password:
            password_key_mgmt = {
                "802-11-wireless-security": {
                    "key-mgmt": "wpa-psk",
                    "psk": config.hotspot_password,
                }
            }

            hs_dict.update(password_key_mgmt)

        return hs_dict
    elif conn_type == config.type_none:
        # No auth/'open' connection.
        return {
            "802-11-wireless": {"mode": "infrastructure", "ssid": ssid},
            "connection": {
                "id": config.ap_name,
                "type": "802-11-wireless",
                "uuid": str(uuid.uuid4()),
            },
            "ipv4": {"method": "auto"},
            "ipv6": {"method": "auto"},
        }
    elif (
        conn_type == config.type_wep
        or conn_type == config.type_wpa
        or conn_type == config.type_wpa2
    ):
        # Hidden, WEP, WPA, WPA2, password required.
        return {
            "802-11-wireless": {
                "mode": "infrastructure",
                "security": "802-11-wireless-security",
                "ssid": ssid,
            },
            "802-11-wireless-security": {
                "key-mgmt": "wpa-psk",
                "psk": password,
            },
            "connection": {
                "id": config.ap_name,
                "type": "802-11-wireless",
                "uuid": str(uuid.uuid4()),
            },
            "ipv4": {"method": "auto"},
            "ipv6": {"method": "auto"},
        }
    elif conn_type == config.type_enterprise:
        # "MIT SECURE" network.
        return {
            "802-11-wireless": {
                "mode": "infrastructure",
                "security": "802-11-wireless-security",
                "ssid": ssid,
            },
            "802-11-wireless-security": {
                "auth-alg": "open",
                "key-mgmt": "wpa-eap",
            },
            "802-1x": {
                "eap": ["peap"],
                "identity": username,
                "password": password,
                "phase2-auth": "mschapv2",
            },
            "connection": {
                "id": config.ap_name,
                "type": "802-11-wireless",
                "uuid": str(uuid.uuid4()),
            },
            "ipv4": {"method": "auto"},
            "ipv6": {"method": "auto"},
        }
    else:
        logger.error("Invalid conn_type.")
        raise WifiInvalidConnectionType
