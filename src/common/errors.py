import config
import logging

# Create custom logger
logger = logging.getLogger('syslog')
syslog = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] - [%(levelname)s] - [%(module)s:'
                              '%(lineno)d] - %(message)s', "%Y-%m-%d %H:%M:%S")
syslog.setFormatter(formatter)
logger.addHandler(syslog)
logger.setLevel(logging.INFO)

# Change default logging mode when in development environmnets
if config.dev_mode:
    logger.setLevel(logging.DEBUG)


# Error classes for Flask-Restful
class WifiConnectionFailed(Exception):
    pass


class WifiHotspotStartFailed(Exception):
    pass


class WifiInvalidConnectionType(Exception):
    pass


class WifiNoSuitableDevice(Exception):
    pass


# Custom error messages for Flask-RESTful to return
errors = {
    "WifiConnectionFailed": {
         "message": "System error while establishing Wi-Fi connection.",
         "status": 500
     },
    "WifiHotspotStartFailed": {
         "message": "System error starting hotspot.",
         "status": 500
     },
    "WifiInvalidConnectionType": {
         "message": "Invalid connection type.",
         "status": 500
     },
    "WifiNoSuitableDevice": {
         "message": "No suitable Wi-Fi device available.",
         "status": 404
     }
}
