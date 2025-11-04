# NDTkit Python API

![Python API for NDTkit](https://img.shields.io/badge/API-Python-blue.svg)
![License](https://img.shields.io/badge/License-Proprietary-green.svg)

This Python API provides a high-level interface to interact with the [NDTkit](https://www.testia.com/product/ndtkit-ut/) desktop application. It allows developers to script and automate NDTkit features remotely, leveraging the full power of the underlying Java application through a simple and pythonic library.

## How it Works ⚙️

The API acts as a client that communicates with a dedicated socket server running within the NDTkit Java application or that uses directly py4j for basic Java API call.

## Prerequisites

Before using this API, you must have:

1.  **Python 3.9+** installed.
2.  The **NDTkit desktop application** installed.
3.  The Java socket server for the API must be running. The Python API can automatically launch it if configured correctly.

## 🚀 Installation & Configuration

1.  **Install the library**

```
pip install ndtkit-api
```

2.  **Configure the connection**: NDTkit and this API are sey with a socket server and a Py4j server that runs on the same IP:PORT, so no change are needed only if this information needs to be expressly changed. If the NDTkit software needs to be launched from an external Python code that embeds this library, it's possible to set the `NDTKIT_FILEPATH` and this API will launch the software automatically if no socket server is detected. Here is an example on how to configure these different variables:

    ```python
    from ndtkit_api.config import config

    config.NDTKIT_FILEPATH = "C:/Users/admin/NDTkit/NDTkit.vbs"
    config.SERVER_HOST = "127.0.0.1"          # default value
    config.SERVER_PORT = 32146              # default value
    config.SERVER_CONNECTION_TIMEOUT = 120  # default value
    ```

    - **`NDTKIT_FILEPATH`**: **This is the most critical setting.** It's the command used to launch the Java socket server. The Python API will execute this command if it cannot connect to the server.
    - **`SERVER_HOST`**: The IP address of the machine running NDTkit. Use `127.0.0.1` if it's on the same machine.
    - **`SERVER_PORT`**: The port for the socket communication. This must match the port the NDTkit server is listening on.
    - **`SERVER_CONNECTION_TIMEOUT`**: After this timing (in seconds) this API will stop attempting to connect to NDTkit's socket server

## Usage Example

Here is a simple example showing how to open a C-Scan, modify a pixel, and save it to a new file.

```python
# examples.py

from ndtkit_api import NDTKitCScanInterface, ndtkit_socket_connection
from ndtkit_api.model.frame.NICartographyFrameCScan import NICartographyFrameCScan


def change_pixel_value(input_file: str, output_file: str):
    """
    Opens a C-Scan, modifies the value of the first pixel, saves it,
    and re-opens it for display.
    """
    print(f"Opening C-Scan: {input_file}")
    # The server is launched automatically if not running
    cscan: NICartographyFrameCScan = NDTKitCScanInterface.open_cscan(input_file)

    if not cscan:
        print("Failed to open C-Scan.")
        return

    print(f"C-Scan opened successfully with UUID: {cscan.get_uuid()}")

    print("Retrieving data matrix...")
    data: list[list[float]] = cscan.get_data()
    print(f"Original value at [0][0]: {data[0][0]}")

    # Modify the data
    data[0][0] = 12.0
    print(f"Setting new value at [0][0] to 12.0")
    cscan.set_data(data)

    print(f"Saving modified C-Scan to: {output_file}")
    NDTKitCScanInterface.save_cscan(cscan, output_file)

    print("Re-opening the saved C-Scan to verify.")
    NDTKitCScanInterface.open_cscan(output_file, displayResult=True)
    print("Done.")


if __name__ == "__main__":
    ndtkit_socket_connection.launch_ndtkit() # Launch NDTkit if it is not already done
    # Make sure to use paths that are valid on your system
    input_cscan_path = "C:/Users/admin/Documents/Data/dd_carto.nkc"
    output_cscan_path = "C:/Users/admin/Documents/Data/result.nkc"
    change_pixel_value(input_cscan_path, output_cscan_path)

```

## A class/method is available in the Java API but it is not appearing in this Python API

It can be reachable anyway, it's just the auto-completion of your IDE that is not working. Actually this Python API is using [py4j](https://www.py4j.org/) that allows to access any Java API function.
Here's an example on how to access to `agi.ndtkit.api.NDTKitCScanInterface.openCScan(String)` without using directly the API:

```python
from ndtkit_api.ndtkit_socket_connection import gateway

gateway.jvm.agi.ndtkit.api.NDTKitCScanInterface.openCScan("path/to/my/cscan") # type: ignore
```

So please refer to the NDTkit Javadoc to have an exhaustive look at all the available actions and call them using this solution if they are not available directly in this Python API.
