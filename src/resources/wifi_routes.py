import config
import dotenv
import threading
from common.errors import logger
from common.wifi import check_internet_status
from common.wifi import check_wifi_status
from common.wifi import connect
from common.wifi import forget
from common.wifi import get_connection_id
from common.wifi import list_access_points
from dotenv import dotenv_values
from flask import request
from flask_restful import Resource


class wifi_connect(Resource):
    def post(self):
        content = request.get_json()

        # If the device is already connected to a wifi network
        if check_wifi_status():
            return {"message": "Device is already connected."}, 409

        # Check for any missing strings
        if "conn_type" not in content or "ssid" not in content:
            return {"message": "Type or SSID not specified"}, 400

        # NetworkManager only supports passwords with minimum 8 character
        # https://gitlab.freedesktop.org/NetworkManager/NetworkManager/-/issues/768
        if "password" in content and len(content["password"]) < 8:
            return {
                "message": "Passwords must be 8 characters or longer."
            }, 400

        # Use threading so the response can be returned before the user is
        # disconnected.
        wifi_connect_thread = threading.Thread(target=connect, kwargs=content)

        wifi_connect_thread.start()

        return {"message": "accepted"}, 202


class wifi_connection_status(Resource):
    def get(self):
        return {
            "wifi": check_wifi_status(),
            "internet": check_internet_status(),
        }


class wifi_forget(Resource):
    def post(self):
        # Check the all_networks boolean
        if not request.get_json() or "all_networks" not in request.get_json():
            # If the device is not connected to a wifi network
            if not check_wifi_status():
                return {"message": "Device is already disconnected."}, 409

            forget_mode = False
        else:
            forget_mode = request.get_json()["all_networks"]

        # Use threading so the response can be returned before the user is
        # disconnected.
        wifi_forget_thread = threading.Thread(
            target=forget,
            kwargs={"create_new_hotspot": True, "all_networks": forget_mode},
        )

        logger.info("Removing connetion...")
        wifi_forget_thread.start()

        return {"message": "accepted"}, 202


class wifi_list_access_points(Resource):
    def get(self):
        ssids, iw_status = list_access_points()

        return {"ssids": ssids, "iw_compatible": iw_status}


class wifi_set_hotspot_password(Resource):
    def post(self):
        content = request.get_json()

        if ("password" not in content) or (len(content["password"]) < 8):
            return {
                "message": "Passwords must be 8 characters or longer."
            }, 400

        if not dotenv_values("db/.db"):
            with open("db/.db", "w") as db:
                db.write("PWC_HOTSPOT_PASSWORD=" + content["password"])
        else:
            dotenv.set_key(
                "db/.db", "PWC_HOTSPOT_PASSWORD", content["password"]
            )

        # Set the new SSID to the global var
        config.hotspot_password = content["password"]

        # Fetch ID of any current connection
        connection = get_connection_id()

        # If there is a running hotspot, recreate it with the new details
        if (
            connection
            and connection.GetSettings()["802-11-wireless"]["mode"] == "ap"
        ):
            wifi_forget_thread = threading.Thread(
                target=forget,
                kwargs={"create_new_hotspot": True},
            )
            wifi_forget_thread.start()

        return {"message": "ok"}, 200


class wifi_set_hotspot_ssid(Resource):
    def post(self):
        content = request.get_json()

        if not dotenv_values("db/.db"):
            with open("db/.db", "w") as db:
                db.write("PWC_HOTSPOT_SSID=" + content["ssid"])
        else:
            dotenv.set_key("db/.db", "PWC_HOTSPOT_SSID", content["ssid"])

        # Set the new SSID to the global var
        config.hotspot_ssid = content["ssid"]

        # Fetch ID of any current connection
        connection = get_connection_id()

        # If there is a running hotspot, recreate it with the new details
        if (
            connection
            and connection.GetSettings()["802-11-wireless"]["mode"] == "ap"
        ):
            wifi_forget_thread = threading.Thread(
                target=forget,
                kwargs={"create_new_hotspot": True},
            )
            wifi_forget_thread.start()

        return {"message": "ok"}, 200


class wifi_set_interface(Resource):
    def post(self):
        # Check entry exists
        if not request.get_json() or "interface" not in request.get_json():
            return {"message": "Interface value not provided."}, 500
        else:
            config.interface = request.get_json()["interface"]
            logger.info(f"Interface changed to {config.interface}")
            return {"message": "ok"}, 200
