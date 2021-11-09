import config
import time
from common.errors import errors
from common.errors import logger
from common.system import dnsmasq
from common.system import led
from common.wifi import auto_connect
from common.wifi import check_wifi_status
from common.wifi import connect
from common.wifi import refresh_networks
from config import host
from config import port
from flask import Flask
from flask_restful import Api
from resources.system_routes import system_health_check
from resources.wifi_routes import wifi_connect
from resources.wifi_routes import wifi_connection_status
from resources.wifi_routes import wifi_forget
from resources.wifi_routes import wifi_list_access_points
from waitress import serve


# Create Flask app instance
app = Flask(__name__)

# Load Flask-Restful API
api = Api(app, errors=errors)

# Health check routes
api.add_resource(system_health_check, '/healthcheck')

# Wi-Fi routes
api.add_resource(wifi_connect, '/v1/connect')
api.add_resource(wifi_connection_status, '/v1/connection_status')
api.add_resource(wifi_forget, '/v1/forget')
api.add_resource(wifi_list_access_points, '/v1/list_access_points')

if __name__ == '__main__':
    # Begin loading program
    logger.info('Checking for previously configured Wi-Fi connections...')

    # Start dnsmasq service for assigning IPs to connected devices
    dnsmasq()

    # Allow time for an exsiting saved Wi-Fi connection to connect.
    time.sleep(10)

    # If the Wi-Fi connection is not already active, start a hotspot
    if check_wifi_status():
        led(1)
        logger.info('Wi-Fi connection already established.')
        logger.info('Ready...')
    else:
        led(0)
        refresh_networks(retries=1)
        if config.auto_connect_kargs:
            logger.info('Attempting auto-connect...')
            auto_connect(**config.auto_connect_kargs)
        else:
            connect()

    serve(app, host=host, port=port)
