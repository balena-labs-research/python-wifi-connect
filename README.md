## Description

An API for controlling Wi-Fi connections on [Balena](https://www.balena.io/os/) devices.

It does not contain a user interface, instead it provides API endpoints to send requests to interact with the device. Any user interface of your choice can be built to interact with the API. If you develop a user interface that is open source, please do let me know so I can provide people links.

## Example user interface

Maintained on a separate repo: https://github.com/balena-labs-research/starter-Interface.
<img width="595" alt="Screenshot 2021-11-10 at 19 24 28" src="https://user-images.githubusercontent.com/64841595/141179620-9358d32f-2a73-426d-91d3-c43ffb8ff316.png">

## Get started

On launch, the app will detect if you already have a Wi-Fi connection. If you do, it will sleep and wait for a command. If you don’t, it will launch a hotspot and wait for a connection from you. Once connected, you can take further actions using the endpoints listed below.

By default, the Wi-Fi SSID is: `Py Wi-Fi Connect`

You can set your own default Wi-Fi SSID and a Wi-Fi password for your hotspot using the environment variables in the docker-compose.yml file.

Enjoy and please do feel free to feedback experiences and issues.

## Automatic connections

You can specify a Wi-Fi connection you would like your device to try and connect to the first time it loads by using the environment variables in the docker-compose.yml file. Once this connection is established, the device will stay connected after reboots until you use the `forget` endpoint. If the network is not available, the hotspot will start instead.

```
PWC_AC_SSID: "network-name" # The SSID of the network you would like to try and auto-connect.
PWC_AC_USERNAME: "username" # Optional, for enterprise networks
PWC_AC_PASSWORD: "your-password" # Optional, the password associated with the Wi-Fi network. Must be 8 characters or more.
```

## Securing the API

By default, the API is exposed so your user interface can interact directly. In other words, anyone can go to `http://your-device:9090/v1/connect` to send commands to your device.

If you would prefer to only allow access from your backend, change the `PWC_HOST` environment variable to `127.0.0.1`. Then ensure your backend container is connected to the host network so it matches the API docker-compose.yml file in this repo:

`network_mode: "host"`

Users will then be unable to access the API `http://your-device:9090/v1/connect`. Your backend container on the device, however, can reach the API using `http://127.0.0.1:9090/v1/connect`. This is useful if your user interface has a login process, and you only want users to be able to interact with Wi-Fi after logging in.

Alternatively, if you would rather have your backend use specified ports instead of the host network, you can change the `PWC_HOST` environment variable to `172.17.0.1` and access the API from `http://172.17.0.1:9090/v1/connect`. On some devices, the default `172.17.0.1` address can not be guaranteed. You can therefore set `PWC_HOST` to `bridge` and it will detect the default Balena Engine bridge on startup and listen on that IP. You wil then need to identify the IP in your other container in order to communicate. The following command in a shell script will get you the IP:

`ip route | awk '/default / { print $3 }'`

## Changing the default network interface

By default, the first available Wi-Fi network interface available will be used. For the vast majority of cases there is only one Wi-Fi network interface and therefore this is no issue. Similarly, if you plug in a Wi-Fi dongle to a device without its own built-in Wi-Fi, the Wi-Fi dongle will be used by default.

If however, you have a device with built in Wi-Fi and a Wi-Fi dongle, you will have a device with two network interfaces. For these instances, or on other occasions where you have a complex network interface setup, you can specify which network interface you would like Py Wi-Fi Connect to use by setting the environment variable shown in the `docker-compose.yml` file:

```
PWC_INTERFACE: "wlan0"
```

To allow for automatic detection, remove the variable from your `docker-compose.yml` file.

This setting can also be controlled using the `/set_interface` endpoint.

## LED Indicator

Some devices - such as the Raspberry Pi series - have an LED that can be controlled. When your device is connected to Wi-Fi, Python Wi-Fi Connect turns the LED on. When disconnected or in Hotspot mode, it turns the LED off.

If you need to disable this feature to allow the LED to be used for other purposes, change the environment variable in the docker-compose.yml file to: `PWC_LED: "OFF"`.

## Endpoints

### http://your-device:9090/v1/connect

Connect to a nearby Wi-Fi access point. Once connected the device will automatically connect to the same network on next boot until you call the `/forget` endpoint.

#### POST

```
{
    "ssid": "BT-Media-543", // Name of the Wi-Fi network you want to connect to.
    "conn_type": "WPA2", // Can be identified from the list_access_points endpoint.
    "username": "username", // Optional for enterprise networks.
    "password": "example-password" // Optional. Minimum 8 characters

}
```

#### Response status 202

Requests are returned immediately and then the process is executed. Otherwise users would be disconnected before they were able to receive the returned response.

```
{
    "message": "accepted"
}
```

### http://your-device:9090/v1/connection_status

Check whether your device is connected to a Wi-Fi hotspot and whether there is internet access.

#### GET

#### Response status 200

```
{
    "wifi": true,
    "internet": true
}
```

### http://your-device:9090/v1/forget

Disconnect from an access point and forget the connection so it will not automatically reconnect on next launch of your device.

When passing `"all_networks": false` this endpoint will only touch Wi-Fi connections set up using this app. If you pass `"all_networks": true` it will remove all Wi-Fi connections from the device. This is useful if you have set up a Wi-Fi connection with another app and need to clear out connections to allow Python-WiFi-Connect to manage connections.

#### POST

```
{
    "all_networks": false
}
```

#### Response status 202

Requests are returned immediately and then the process is executed. Otherwise users would be disconnected before they were able to receive the returned response.

```
{
    "message": "accepted"
}
```

### http://your-device:9090/v1/list_access_points

Fetch list of nearby Wi-Fi networks for passing to the connect endpoint.

#### GET

#### Response status 200

```
{
    "ssids": [
        {
            "ssid": "VM123934", // SSID of the device
            "conn_type": "WPA2", // Security type.
            "strength": 100 // Signal strength from 0 – 100, with 100 being strongest
        },
        {
            "ssid": "BT Media",
            "conn_type": "ENTERPRISE",
            "strength": 70
        },
        {
            "ssid": "Althaea-2-no-password",
            "security": "NONE",
            "strength": 65
        },
        {
            "ssid": "TELUS9052-Hidden",
            "security": "HIDDEN",
            "strength": 10
        }
    ],
    "iw_compatible": true // Whether your device supports refreshing
    // of the nearby networks using IW (True = it does support it).
    // When this is false, your device may need to be restarted to refresh
    // the networks list. When it is True, you may be able to refresh the
    // links by calling the list_access_points endpoint again. Useful for
    // enabling or disabling a refresh button on a user interface.
}
```

### http://your-device:9090/v1/healthcheck

Check whether the API is available. Accessing this path will not log anything in the console.

#### GET

#### Response status 200

```
{
    "message": "ok"
}
```

### http://your-device:9090/v1/set_hotspot_password

Allows setting the hotspot password. Using this endpoint will store the passed string in a file and will override the environment variable password. Ensure the `./db` folder is mounted as a volume for this change to be persistent.

#### POST

```
{
    "password": "new-password" // Minimum of 8 characters
}
```

#### Response status 200

```
{
    "message": "ok"
}
```

### http://your-device:9090/v1/set_hotspot_ssid

Allows setting the hotspot SSID. Using this endpoint will store the passed string in a file and will override any environment variable ssid. Ensure the `./db` folder is mounted as a volume for this change to be persistent.

#### POST

```
{
    "ssid": "new SSID"
}
```

#### Response status 200

```
{
    "message": "ok"
}
```

### http://your-device:9090/v1/set_interface

By default the Wi-Fi network interface is auto-detected. If you need to specify a network interface, you can do so using this endpoint.

Changing the setting will only last until the next restart of the container, when it will resort back to the setting set by the environment variable in the container or detect the interface automatically if there is no environment variable in the container.

#### POST

```
{
    "interface": "wlan0"
}
```

#### Response status 200

```
{
    "message": "ok"
}
```
