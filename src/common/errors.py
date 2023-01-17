import config
import logging

# Create custom logger
syslog = logging.StreamHandler()
logger = logging.getLogger("syslog")
logger.addHandler(syslog)

# When in development mode provide details in log of each line of code
# that is executing
if config.dev_mode is True:
    formatter = logging.Formatter(
        "[%(asctime)s] - [%(levelname)s] - "
        "[%(module)s:%(lineno)d] - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    logger.setLevel(logging.DEBUG)
else:
    formatter = logging.Formatter(
        "[%(asctime)s] - [%(levelname)s] - " "%(message)s", "%Y-%m-%d %H:%M:%S"
    )
    logger.setLevel(logging.INFO)

syslog.setFormatter(formatter)
logger.propagate = False


# Error classes for Flask-Restful
class WifiConnectionFailed(Exception):
    pass


class WifiDeviceNotFound(Exception):
    pass


class WifiHotspotStartFailed(Exception):
    pass


class WifiInvalidConnectionType(Exception):
    pass


class WifiNetworkManagerError(Exception):
    pass


# Custom error messages for Flask-RESTful to return
errors = {
    "WifiConnectionFailed": {
        "message": "System error while establishing Wi-Fi connection.",
        "status": 500,
    },
    "WifiDeviceNotFound": {
        "message": "Requested device not available.",
        "status": 500,
    },
    "WifiHotspotStartFailed": {
        "message": "System error starting hotspot.",
        "status": 500,
    },
    "WifiInvalidConnectionType": {
        "message": "Invalid connection type.",
        "status": 500,
    },
    "WifiNetworkManagerError": {
        "message": "Failed communicating with Network Manager.",
        "status": 500,
    },
}
