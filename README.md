## Description

An API for controlling Wi-Fi connections on [Balena](https://www.balena.io/os/) devices.

It does not contain an interface, instead it provides API endpoints to send requests to interact with the device. Any interface of your choice can be built to interact with the API. If you develop an interface that is open source, please do let me know so I can provide people links. 

## Get started
On launch, the app will detect if you already have a Wi-Fi connection. If you do, it will sleep and wait for a command. If you don’t, it will launch a hotspot and wait for a connection from you. Once connected, you can take further actions using the endpoints listed below.

By default, the Wi-Fi SSID is: `Py Wi-Fi Connect`

You can set your own default Wi-Fi SSID and a Wi-Fi password for your hotspot using the environment variables in the docker-compose.yml file.

Enjoy and please do feel free to feedback experiences and issues.

## Securing the API

By default, the API is exposed so your interface can interact directly. In other words, anyone can go to `http://your-device:9090/v1/connect` to send commands to your device. 

If you would prefer to only allow access from your backend, change the `host` environment variable to `127.0.0.1`. Then ensure your backend container is connected to the host network so it matches the API docker-compose.yml file in this repo:

`network_mode: "host"`

Users will then be unable to access the API `http://your-device:9090/v1/connect`. Your backend container on the device, however, can reach the API using `http://127.0.0.1:9090/v1/connect`. This is useful if your interface has a login process, and you only want users to be able to interact with Wi-Fi after logging in.

Alternatively, if you would rather have your backend use specified ports instead of the host network, you can change the `host` environment variable to `172.17.0.1` and access the API from `http://172.17.0.1:9090/v1/connect`.


## Endpoints

### http://your-device:9090/v1/connect
Connect to a nearby Wi-Fi access point.

#### POST
````
{
    "ssid": "BT-Media-543", // Name of the Wi-Fi network you want to connect to.
    "conn_type": "WPA2", // Can be identified from the list_access_points endpoint.
    "username": "username", // Optional for enterprise networks.
    "password": "example-password" // Optional. Minimum 8 characters

}
````

#### Response status 202
Requests are returned immediately and then the process is executed. Otherwise users would be disconnected before they were able to receive the returned response. 
````
{
    "message": "accepted"
}
````

### http://your-device:9090/v1/connection_status

Check whether your device is connected to a Wi-Fi hotspot and whether there is internet access.
#### GET

#### Response status 200
````
{
    "wifi": true,
    "internet": true
}
````

### http://your-device:9090/v1/forget

Disconnect from the access point you earlier connected to with this app and forget the connection so it will not automatically reconnect on next launch of your device.
#### GET

#### Response status 202
Requests are returned immediately and then the process is executed. Otherwise users would be disconnected before they were able to receive the returned response. 
````
{
    "message": "accepted"
}
````

### http://your-device:9090/v1/list_access_points

Fetch list of nearby Wi-Fi networks for passing to the connect endpoint.
#### GET

#### Response status 200
````
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
    // enabling or disabling a refresh button on an interface.
}
````

### http://your-device:9090/v1/healthcheck
Check whether the API is available. Accessing this path will not record anything in the console.

#### GET

#### Response status 200
Requests are returned immediately and then the process is executed. Otherwise users would be disconnected before they were able to receive the returned response. 
````
{
    "message": "ok"
}
````