import config
import NetworkManager
import socket
import subprocess
import time
import uuid
from common.errors import logger
from common.errors import WifiConnectionFailed
from common.errors import WifiHotspotStartFailed
from common.errors import WifiInvalidConnectionType
from common.errors import WifiNoSuitableDevice


# Import DBus mainloop for NetworkManager use
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)


def check_internet_status(host="8.8.8.8", port=53, timeout=5):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        # If there is a connection return True
        return True
    except socket.error:
        # If there isn't a connection return False
        return False


def check_wifi_status():
    try:
        run = subprocess.run(["iw", "dev", "wlan0", "link"],
                             capture_output=True,
                             text=True).stdout.rstrip()
    except Exception:
        logger.exception("Failed checking connection. Returning False to"
                         "allow hotspot to start.")
        return False

    if run.lower()[:13] == "not connected":
        return False
    else:
        return True


def connect(conn_type=config.type_hotspot,
            ssid=None,
            username=None,
            password=None):
    # Remove any existing connection made by this app
    forget()

    # If user has specified a password for their hotspot
    if conn_type == config.type_hotspot and config.hotspot_password:
        password = config.hotspot_password

    try:
        # Hotspot for user to connect to device
        hotspot_dict = {
            '802-11-wireless': {'band': 'bg',
                                'mode': 'ap',
                                'ssid': config.hotspot_ssid},
            'connection': {'autoconnect': False,
                           'id': config.ap_name,
                           'interface-name': 'wlan0',
                           'type': '802-11-wireless',
                           'uuid': str(uuid.uuid4())},
            'ipv4': {'address-data':
                     [{'address': '192.168.42.1', 'prefix': 24}],
                     'addresses': [['192.168.42.1', 24, '0.0.0.0']],
                     'method': 'manual'},
            'ipv6': {'method': 'auto'}
        }

        # Include a key-mgmt string in hotspot if setting a password
        if password:
            password_key_mgmt = {'802-11-wireless-security':
                                 {'key-mgmt': 'wpa-psk', 'psk': password}}

            hotspot_dict.update(password_key_mgmt)

        # "MIT SECURE" network.
        enterprise_dict = {
            '802-11-wireless': {'mode': 'infrastructure',
                                'security': '802-11-wireless-security',
                                'ssid': ssid},
            '802-11-wireless-security':
                {'auth-alg': 'open', 'key-mgmt': 'wpa-eap'},
            '802-1x': {'eap': ['peap'],
                       'identity': username,
                       'password': password,
                       'phase2-auth': 'mschapv2'},
            'connection': {'id': config.ap_name,
                           'type': '802-11-wireless',
                           'uuid': str(uuid.uuid4())},
            'ipv4': {'method': 'auto'},
            'ipv6': {'method': 'auto'}
        }

        # No auth/'open' connection.
        no_auth_dict = {
            '802-11-wireless': {'mode': 'infrastructure',
                                'ssid': ssid},
            'connection': {'id': config.ap_name,
                           'type': '802-11-wireless',
                           'uuid': str(uuid.uuid4())},
            'ipv4': {'method': 'auto'},
            'ipv6': {'method': 'auto'}
        }

        # Hidden, WEP, WPA, WPA2, password required.
        passwd_dict = {
            '802-11-wireless': {'mode': 'infrastructure',
                                'security': '802-11-wireless-security',
                                'ssid': ssid},
            '802-11-wireless-security':
                {'key-mgmt': 'wpa-psk', 'psk': password},
            'connection': {'id': config.ap_name,
                           'type': '802-11-wireless',
                           'uuid': str(uuid.uuid4())},
            'ipv4': {'method': 'auto'},
            'ipv6': {'method': 'auto'}
        }

        if conn_type == config.type_hotspot:
            conn_dict = hotspot_dict
        elif conn_type == config.type_none:
            conn_dict = no_auth_dict
        elif (conn_type == config.type_wep or
                conn_type == config.type_wpa or
                conn_type == config.type_wpa2):
            conn_dict = passwd_dict
        elif conn_type == config.type_enterprise:
            conn_dict = enterprise_dict
        else:
            logger.error("Invalid conn_type.")
            raise WifiInvalidConnectionType

        NetworkManager.Settings.AddConnection(conn_dict)
        logger.info(f"Added connection of type {conn_type}")

        # Find this connection and its device
        connections = NetworkManager.Settings.ListConnections()
        connections = dict([(x.GetSettings()['connection']['id'], x)
                            for x in connections])
        conn = connections[config.ap_name]

        # Find a suitable device
        ctype = conn.GetSettings()['connection']['type']
        dtype = {'802-11-wireless': NetworkManager.NM_DEVICE_TYPE_WIFI} \
            .get(ctype, ctype)
        devices = NetworkManager.NetworkManager.GetDevices()

        for dev in devices:
            if dev.DeviceType == dtype:
                break
        else:
            logger.error(f"No suitable and available {ctype} device found")
            raise WifiNoSuitableDevice

        # Connect
        NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")
        logger.info("Activated connection.")

        # Wait for ADDRCONF(NETDEV_CHANGE): wlan0: link becomes ready
        logger.info("Waiting for connection to become active...")
        loop_count = 0
        while dev.State != NetworkManager.NM_DEVICE_STATE_ACTIVATED:
            time.sleep(1)
            loop_count += 1
            if loop_count > 30:  # Only wait 30 seconds max
                break

        if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
            logger.info("Connection is live.")
            return True
        # If the current attempt is not already a hotspot attempt
        elif conn_type != config.type_hotspot:
            # Restart hotspot as connection failed
            logger.warning("Connection attempt failed.")
            connect()
        else:
            raise WifiHotspotStartFailed
    except Exception:
        logger.exception("Connection failed.")
        # If the current attempt is not already a hotspot attempt
        if conn_type == config.type_hotspot:
            raise WifiHotspotStartFailed
        else:
            connect()  # Restart hotspot as connection failed
            raise WifiConnectionFailed


def dnsmasq():
    # Build the list of args
    path = "/usr/sbin/dnsmasq"
    args = [path]
    args.append(f"--address=/#/{config.DEFAULT_GATEWAY}")
    args.append(f"--dhcp-range={config.DEFAULT_DHCP_RANGE}")
    args.append(f"--dhcp-option=option:router,{config.DEFAULT_GATEWAY}")
    args.append(f"--interface={config.DEFAULT_INTERFACE}")
    args.append("--keep-in-foreground")
    args.append("--bind-dynamic")
    args.append("--except-interface=lo")
    args.append("--conf-file")
    args.append("--no-hosts")

    try:
        subprocess.Popen(args)
    except Exception:
        logger.exception('Failed to start dnsmasq.')
        # Allow pass to facilitate software updates


def forget(create_new_hotspot=False):
    # Find and delete the hotspot connection
    try:
        connections = NetworkManager.Settings.ListConnections()
        connections = dict([(x.GetSettings()['connection']['id'], x)
                            for x in connections])

        if config.ap_name in connections:
            conn = connections[config.ap_name]
            conn.Delete()

        if create_new_hotspot:
            refresh_networks()
            connect()

    except Exception:
        logger.exception("Failed to delete network.")
        return False

    return True


def list_access_points():
    # Run IW to reduce chance of empty SSID list. Storing result
    # to return so that if IW does not work on this device the refresh
    # button will be disabled.
    iw_status = refresh_networks(retries=1)

    ssids = []  # List to be returned

    for dev in NetworkManager.NetworkManager.GetDevices():
        if dev.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
            continue
        for ap in dev.GetAccessPoints():
            security = config.type_none

            # Based on a subset of the AP_SEC flag settings
            # (https://developer.gnome.org/NetworkManager/1.2/nm-dbus-types.html#NM80211ApSecurityFlags)
            # determine which type of security this AP uses.
            AP_SEC = NetworkManager.NM_802_11_AP_SEC_NONE
            if ap.Flags & NetworkManager.NM_802_11_AP_FLAGS_PRIVACY and \
                    ap.WpaFlags == AP_SEC and \
                    ap.RsnFlags == AP_SEC:
                security = config.type_wep

            if ap.WpaFlags != AP_SEC:
                security = config.type_wpa

            if ap.RsnFlags != AP_SEC:
                security = config.type_wpa2

            if ap.WpaFlags & \
                NetworkManager.NM_802_11_AP_SEC_KEY_MGMT_802_1X or \
                    ap.RsnFlags & \
                    NetworkManager.NM_802_11_AP_SEC_KEY_MGMT_802_1X:
                security = config.type_enterprise

            entry = {"ssid": ap.Ssid,
                     "conn_type": security,
                     "strength": int(ap.Strength)}

            # Do not add duplicates to the list
            if ssids.__contains__(entry):
                continue

            # Do not add own hotspot to the list
            if ap.Ssid == config.hotspot_ssid:
                continue

            ssids.append(entry)

        # Sort SSIDs by signal strength
        ssids = sorted(ssids,
                       key=lambda x: x['strength'],
                       reverse=True)

    # Return a list of available SSIDs and their security type,
    # or [] for none available or error.
    return ssids, iw_status


def refresh_networks(retries=5):
    # Refreshing networks list using IW which has proven
    # to be better at refreshing than nmcli. Some devices
    # do not support this feature while the AP is active
    # and therefore returns a boolean with status of request.

    # After forget has run, NetworkManager takes a while to release
    # the Wi-Fi for iw to use it, hence the retries.
    max_runs = retries
    run = 0
    while run < max_runs:
        try:
            time.sleep(3)
            subprocess.check_output(["iw", "dev", "wlan0", "scan"])
        except subprocess.CalledProcessError:
            logger.warning('Resource busy. Retrying...')
            continue
        except Exception:
            logger.error('Unknown error calling IW.')
            return False
        else:
            logger.info('IW succeeded.')
            return True
        finally:
            run += 1

    logger.warning("IW is not accessible. This can happen on some devices "
                   "and is usually nothing to worry about.")
    return False
