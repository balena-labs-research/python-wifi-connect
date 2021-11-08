import threading
from common.wifi import check_internet_status
from common.wifi import check_wifi_status
from common.wifi import connect
from common.wifi import forget
from common.wifi import list_access_points
from flask import request
from flask_restful import Resource


class wifi_connect(Resource):
    def post(self):
        content = request.get_json()

        # If the device is already connected to a wifi network
        if check_wifi_status():
            return {'message': 'Device is already connected.'}, 409

        # Check for any missing strings
        if "conn_type" not in content or "ssid" not in content:
            return {'message': 'Type or SSID not specified'}, 400

        # NetworkManager only supports passwords with minimum 8 character
        # https://gitlab.freedesktop.org/NetworkManager/NetworkManager/-/issues/768
        if 'password' in content and len(content['password']) < 8:
            return {'message': 'Passwords must be 8 characters or longer.'}, \
                   400

        # Use threading so the response can be returned before the user is
        # disconnected.
        wifi_connect_thread = threading.Thread(target=connect,
                                               kwargs=content)

        wifi_connect_thread.start()

        return {'message': 'accepted'}, 202


class wifi_connection_status(Resource):
    def get(self):
        return {'wifi': check_wifi_status(),
                'internet': check_internet_status()}


class wifi_forget(Resource):
    def post(self):
        # If the device is not connected to a wifi network
        if not check_wifi_status():
            return {'message': 'Device is already disconnected.'}, 409

        # Check the all_networks boolean is valid
        if (not request.get_json() or
            'all_networks' not in request.get_json()
                or type(request.get_json()['all_networks']) is not bool):
            return {'message': "all_networks boolean missing or is not "
                               "a boolean."}, 202

        # Use threading so the response can be returned before the user is
        # disconnected.
        wifi_forget_thread = threading.Thread(target=forget,
                                              kwargs={'create_new_hotspot':
                                                      True,
                                                      'all_networks':
                                                      request.get_json()
                                                      ['all_networks']})

        wifi_forget_thread.start()

        return {'message': 'accepted'}, 202


class wifi_list_access_points(Resource):
    def get(self):
        ssids, iw_status = list_access_points()

        return {'ssids': ssids, 'iw_compatible': iw_status}
