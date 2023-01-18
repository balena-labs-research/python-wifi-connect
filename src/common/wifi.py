import config
import NetworkManager as Pnm  # Python NetworkManager
import os
import socket
import subprocess
import sys
import time
from common.errors import logger
from common.errors import WifiConnectionFailed
from common.errors import WifiDeviceNotFound
from common.errors import WifiHotspotStartFailed
from common.errors import WifiNetworkManagerError
from common.nm_dicts import get_nm_dict
from common.system import led
from time import sleep


def analyse_access_point(ap):
    security = config.type_none

    # Based on a subset of the AP_SEC flag settings
    # (https://developer.gnome.org/NetworkManager/1.2/nm-dbus-types.html#NM80211ApSecurityFlags)
    # to determine which type of security this AP uses.
    AP_SEC = Pnm.NM_802_11_AP_SEC_NONE
    if (
        ap.Flags & Pnm.NM_802_11_AP_FLAGS_PRIVACY
        and ap.WpaFlags == AP_SEC
        and ap.RsnFlags == AP_SEC
    ):
        security = config.type_wep

    if ap.WpaFlags != AP_SEC:
        security = config.type_wpa

    if ap.RsnFlags != AP_SEC:
        security = config.type_wpa2

    if (
        ap.WpaFlags & Pnm.NM_802_11_AP_SEC_KEY_MGMT_802_1X
        or ap.RsnFlags & Pnm.NM_802_11_AP_SEC_KEY_MGMT_802_1X
    ):
        security = config.type_enterprise

    entry = {
        "ssid": ap.Ssid,
        "conn_type": security,
        "strength": int(ap.Strength),
    }

    return entry


def auto_connect(ssid=None, username=None, password=None):
    ssids, _ = list_access_points()

    for ssid_item in ssids:
        if ssid_item["ssid"] == ssid:
            connect(
                conn_type=ssid_item["conn_type"],
                ssid=ssid,
                username=username,
                password=password,
            )
            break
    else:
        logger.info(
            "Auto-connect failed as the device could not find the "
            "specified network. Starting hotspot instead..."
        )
        connect()


# Returns True when a connection to a router is made, or the Hotspot is live
def check_device_state():
    if get_device().State == Pnm.NM_DEVICE_STATE_ACTIVATED:
        return True
    else:
        return False


# Ignores device and Wi-Fi status and checks for internet. Helpful for when
# connected to Ethernet.
def check_internet_status(host="8.8.8.8", port=53, timeout=5):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        # If there is a connection return True
        return True
    except socket.error:
        # If there isn't a connection return False
        return False


# Checks if there is an active connection to an external Wi-Fi router
def check_wifi_status():
    try:
        run = subprocess.run(
            ["iw", "dev", config.interface, "link"],
            capture_output=True,
            text=True,
        ).stdout.rstrip()
    except Exception:
        logger.exception(
            "Failed checking connection. Returning False to"
            "allow hotspot to start."
        )
        return False

    if run.lower()[:13] == "not connected":
        return False
    else:
        return True


def connect(
    conn_type=config.type_hotspot, ssid=None, username=None, password=None
):
    # Remove any existing connection made by this app
    forget()

    # Get the correct config based on type requested
    logger.info(f"Adding connection of type {conn_type}")
    conn_dict = get_nm_dict(conn_type, ssid, username, password)

    try:
        Pnm.Settings.AddConnection(conn_dict)

        # Connect
        Pnm.NetworkManager.ActivateConnection(
            get_connection_id(), get_device(), "/"
        )

        # If not a hotspot, log the connection SSID being attempted
        if conn_type != config.type_hotspot:
            logger.info(f"Attempting connection to {ssid}")

        # Wait for ADDRCONF(NETDEV_CHANGE): link becomes ready
        loop_count = 0
        while not check_device_state():
            time.sleep(1)
            loop_count += 1
            if loop_count > 30:  # Only wait 30 seconds max
                break

        if check_device_state():
            logger.info("Connection active.")

            # Activate the LED to indicate device is connected.
            if conn_type is not config.type_hotspot:
                led(1)
            else:
                led(0)

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
        if all_networks:
            for connection in Pnm.Settings.ListConnections():
                if (
                    connection.GetSettings()["connection"]["type"]
                    == "802-11-wireless"
                ):
                    # Delete the identified connection
                    network_id = connection.GetSettings()["connection"]["id"]
                    # Add short delay to ensure the endpoint has returned a
                    # response before disconnecting the user.
                    sleep(0.5)
                    connection.Delete()
                    logger.debug(f"Deleted connection: {network_id}")
        else:
            connection_id = get_connection_id()
            # connection_id returns false if it is missing. This can be ignored
            # as this function is often called as a precautionary clean up
            if connection_id:
                # Add short delay to ensure the endpoint has returned a
                # response before disconnecting the user.
                sleep(0.5)
                connection_id.Delete()
                logger.debug(f"Deleted connection: {config.ap_name}")

        # Disable LED indicating Wi-Fi is not active.
        led(0)

        # If requested, create new Hotspot
        if create_new_hotspot:
            refresh_networks()
            connect()

    except Exception:
        logger.exception("Failed to delete network.")
        raise WifiNetworkManagerError

    return True


def get_connection_id():
    connection = dict(
        [
            (x.GetSettings()["connection"]["id"], x)
            for x in Pnm.Settings.ListConnections()
        ]
    )

    if config.ap_name in connection:
        return connection[config.ap_name]
    else:
        return False


def get_device():
    # Configured interface variable takes precedent.
    if "PWC_INTERFACE" in os.environ:
        logger.debug(f"Interface {os.environ['PWC_INTERFACE']} selected.")
        for device in Pnm.NetworkManager.GetDevices():
            if device.DeviceType != Pnm.NM_DEVICE_TYPE_WIFI:
                continue
            # For each Wi-Fi network interface, check the interface name
            # against the one configured in config.interface
            if (
                device.Udi[device.Udi.rfind("/") + 1 :].lower()
                == os.environ["PWC_INTERFACE"]
            ):
                return device

        # If device was not found during the loop
        raise WifiDeviceNotFound

    # Fetch last Wi-Fi interface found
    devices = dict(
        [(x.DeviceType, x) for x in Pnm.NetworkManager.GetDevices()]
    )

    if Pnm.NM_DEVICE_TYPE_WIFI in devices:
        return devices[Pnm.NM_DEVICE_TYPE_WIFI]
    else:
        logger.error("No suitable or available WiFi device found. Exiting.")
        sys.exit(0)


def list_access_points():
    # Run IW to reduce chance of empty SSID list. Storing result
    # to return so that if IW does not work on this device the refresh
    # button will be disabled.
    iw_status = refresh_networks(retries=1)

    logger.debug("Fetching Wi-Fi networks.")

    try:
        # For each wi-fi connection in range, identify it's details
        compiled_ssids = [
            analyse_access_point(ap) for ap in get_device().GetAccessPoints()
        ]
    except Exception:
        logger.exception("Failed listing access points.")
        raise WifiNetworkManagerError

    # Sort SSIDs by signal strength
    compiled_ssids = sorted(
        compiled_ssids, key=lambda x: x["strength"], reverse=True
    )

    # Remove duplicates and own hotspot from list.
    tmp = []
    ssids = []
    for item in compiled_ssids:
        if item["ssid"] not in tmp and item["ssid"] != config.hotspot_ssid:
            ssids.append(item)
        tmp.append(item["ssid"])

    logger.debug("Finished fetching Wi-Fi networks.")

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
            subprocess.check_output(["iw", "dev", config.interface, "scan"])
        except subprocess.CalledProcessError:
            logger.warning("IW resource busy. Retrying...")
            continue
        except Exception:
            logger.error("Unknown error calling IW.")
            return False
        else:
            logger.debug("IW succeeded.")
            return True
        finally:
            run += 1

    logger.warning(
        "IW is unable to complete the request. This can happen on some devices "
        "and is usually nothing to worry about."
    )
    return False
