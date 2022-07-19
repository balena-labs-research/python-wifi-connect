import config
import os
import time
from common.errors import errors
from common.errors import logger
from common.system import dnsmasq
from common.system import led
from common.wifi import auto_connect
from common.wifi import check_device_state
from common.wifi import check_wifi_status
from common.wifi import connect
from common.wifi import get_device
from common.wifi import refresh_networks
from config import host
from config import port
from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from resources.system_routes import system_health_check
from resources.wifi_routes import wifi_connect
from resources.wifi_routes import wifi_connection_status
from resources.wifi_routes import wifi_forget
from resources.wifi_routes import wifi_list_access_points
from resources.wifi_routes import wifi_set_hotspot_password
from resources.wifi_routes import wifi_set_hotspot_ssid
from resources.wifi_routes import wifi_set_interface
from waitress import serve

# Set default interface
device = get_device()
config.interface = device.Udi[device.Udi.rfind("/") + 1 :].lower()

# Create Flask app instance
app = Flask(__name__)

# Allow CORS
CORS(app)

# Load Flask-Restful API
api = Api(app, errors=errors)

# Begin loading program
logger.info("Checking for previously configured Wi-Fi connections...")

# Start dnsmasq service for assigning IPs to connected devices
dnsmasq()

# Allow time for an exsiting saved Wi-Fi connection to connect.
time.sleep(10)

# Log interface status
if "PWC_INTERFACE" in os.environ:
    logger.info(f"Interface set to {os.environ['PWC_INTERFACE']}")

# If the Wi-Fi connection or device is already active, do nothing
if check_wifi_status() or check_device_state():
    led(1)
    logger.info("A Wi-Fi connection or hotspot is already active.")
    logger.info("Ready...")
# If the Wi-Fi connection and device are not active, start a hotspot
else:
    led(0)
    refresh_networks(retries=1)
    if config.auto_connect_kargs:
        logger.info("Attempting auto-connect...")
        auto_connect(**config.auto_connect_kargs)
    else:
        connect()

# Health check routes
api.add_resource(system_health_check, "/healthcheck")

# Wi-Fi routes
api.add_resource(wifi_connect, "/v1/connect")
api.add_resource(wifi_connection_status, "/v1/connection_status")
api.add_resource(wifi_forget, "/v1/forget")
api.add_resource(wifi_list_access_points, "/v1/list_access_points")
api.add_resource(wifi_set_hotspot_password, "/v1/set_hotspot_password")
api.add_resource(wifi_set_hotspot_ssid, "/v1/set_hotspot_ssid")
api.add_resource(wifi_set_interface, "/v1/set_interface")

logger.info(f"Listening on {host} port {port}")
serve(app, host=host, port=port)
