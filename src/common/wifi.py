import config
import NetworkManager
import socket
import subprocess
import time
from common.errors import logger
from common.errors import WifiConnectionFailed
from common.errors import WifiHotspotStartFailed
from common.errors import WifiNetworkManagerError
from common.errors import WifiNoSuitableDevice
from common.nm_dicts import get_nm_dict


# Import DBus mainloop for NetworkManager use
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)


def analyse_access_point(ap):
    security = config.type_none

    # Based on a subset of the AP_SEC flag settings
    # (https://developer.gnome.org/NetworkManager/1.2/nm-dbus-types.html#NM80211ApSecurityFlags)
    # to determine which type of security this AP uses.
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

    return entry


def auto_connect(ssid=None,
                 username=None,
                 password=None):
    ssids, _ = list_access_points()

    for ssid_item in ssids:
        if ssid_item['ssid'] == ssid:
            connect(conn_type=ssid_item['conn_type'],
                    ssid=ssid,
                    username=username,
                    password=password)
            break
    else:
        logger.info('Auto-connect failed as the device could not find the '
                    'specified network.')
        connect()


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

    # Get the correct config based on type requested
    conn_dict = get_nm_dict(conn_type, ssid, username, password)

    try:
        NetworkManager.Settings.AddConnection(conn_dict)
        logger.info(f"Added connection of type {conn_type}")

        # Find this connection and its device
        connections = \
            dict([(x.GetSettings()['connection']['id'], x)
                 for x in NetworkManager.Settings.ListConnections()])
        conn = connections[config.ap_name]

        # Save the wi-fi device object to a variable
        devices = dict([(x.DeviceType, x)
                        for x in NetworkManager.NetworkManager.GetDevices()])

        if NetworkManager.NM_DEVICE_TYPE_WIFI in devices:
            dev = devices[NetworkManager.NM_DEVICE_TYPE_WIFI]
        else:
            logger.error("No suitable and available device found")
            raise WifiNoSuitableDevice

        # Connect
        NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")

        # Wait for ADDRCONF(NETDEV_CHANGE): wlan0: link becomes ready
        logger.info("Waiting for connection to become active...")
        loop_count = 0
        while dev.State != NetworkManager.NM_DEVICE_STATE_ACTIVATED:
            time.sleep(1)
            loop_count += 1
            if loop_count > 30:  # Only wait 30 seconds max
                break

        if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
            logger.info("Connected.")
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


def forget(create_new_hotspot=False, all_networks=False):
    # Find and delete the hotspot connection
    try:
        connections = NetworkManager.Settings.ListConnections()

        if all_networks:
            for connection in connections:
                if connection.GetSettings()["connection"]["type"] \
                        == "802-11-wireless":
                    # Delete the identified connection
                    network_id = connection.GetSettings()["connection"]["id"]
                    connection.Delete()
                    logger.info(f"Deleted connection: {network_id}")
        else:
            connection_ids = \
                dict([(x.GetSettings()['connection']['id'], x)
                     for x in connections])
            if config.ap_name in connection_ids:
                connection_ids[config.ap_name].Delete()
                logger.info(f"Deleted connection: {config.ap_name}")

        if create_new_hotspot:
            refresh_networks()
            connect()

    except Exception:
        logger.exception("Failed to delete network.")
        raise WifiNetworkManagerError

    return True


def list_access_points():
    # Run IW to reduce chance of empty SSID list. Storing result
    # to return so that if IW does not work on this device the refresh
    # button will be disabled.
    iw_status = refresh_networks(retries=1)

    try:
        # Fetch dictionary of devices
        devices = dict([(x.DeviceType, x)
                        for x in NetworkManager.NetworkManager.GetDevices()])

        # Save the wi-fi device object to a variable
        if NetworkManager.NM_DEVICE_TYPE_WIFI in devices:
            dev = devices[NetworkManager.NM_DEVICE_TYPE_WIFI]
        else:
            logger.error("No suitable and available device found")
            raise WifiNoSuitableDevice

        # For each wi-fi connection in range, identify it's details
        compiled_ssids = [analyse_access_point(ap)
                          for ap in dev.GetAccessPoints()]
    except Exception:
        logger.exception('Failed listing access points.')
        raise WifiNetworkManagerError

    # Sort SSIDs by signal strength
    compiled_ssids = sorted(compiled_ssids,
                            key=lambda x: x['strength'],
                            reverse=True)

    # Remove duplicates and own hotspot from list.
    tmp = []
    ssids = []
    for item in compiled_ssids:
        if item['ssid'] not in tmp and item['ssid'] != config.hotspot_ssid:
            ssids.append(item)
        tmp.append(item['ssid'])

    # Return a list of available SSIDs and their security type,
    # or [] for none available.
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
            logger.debug('IW succeeded.')
            return True
        finally:
            run += 1

    logger.warning("IW is not accessible. This can happen on some devices "
                   "and is usually nothing to worry about.")
    return False
