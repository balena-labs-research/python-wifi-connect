import atexit
import signal
import sys
import time
from common.errors import errors
from common.errors import logger
from common.wifi import check_wifi_status
from common.wifi import dnsmasq
from common.wifi import start_hotspot
from resources.system_routes import system_health_check
from resources.wifi_routes import wifi_connect
from resources.wifi_routes import wifi_connection_status
from resources.wifi_routes import wifi_forget
from resources.wifi_routes import wifi_list_access_points
from flask import Flask
from flask_restful import Api


def handle_exit(*args):
    logger.info('Finshed the exit process.')


def handle_sigterm(*args):
    sys.exit(0)


# Startup process
if __name__ == '__main__':
    # Load Flask-Restful API
    api = Api(errors=errors)

    # Create Flask app instance
    app = Flask(__name__)

    # Ensure soft shutdown to terminate wifi-connect
    atexit.register(handle_exit, None, None)
    signal.signal(signal.SIGHUP, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)
    signal.signal(signal.SIGTERM, handle_sigterm)

    # Start dnsmasq service for assigning IPs to connected devices
    dnsmasq()

    # Start hotspot if no wi-fi connection after delay
    time.sleep(10)

    # If the Wi-Fi connection is not already active, start a hotspot
    if check_wifi_status():
        logger.info('Wi-Fi connection already established.')
    else:
        logger.info('Starting hotspot...')
        start_hotspot()

    # Configure endpoints #

    # Health check
    api.add_resource(system_health_check, '/')

    # Wi-Fi
    api.add_resource(wifi_connect, '/v1/connect')
    api.add_resource(wifi_connection_status, '/v1/connection_status')
    api.add_resource(wifi_forget, '/v1/forget')
    api.add_resource(wifi_list_access_points, '/v1/list_access_points')

    # Initialise and start
    api.init_app(app)

    app.run(port=9090, host='0.0.0.0')
