# CANopen for CircuitPython
A simple and robust implementation of the CANopen protocol designed specifically for CircuitPython environments.

## Overview
CANopen for CircuitPython aims to bring the robust and efficient communication of the CANopen protocol to devices running CircuitPython. With a modular design and clear API, this library makes it easy to integrate CANopen communication in your projects.

## Features
**NMT (Network Management)**: Complete state machine implementation allowing nodes to transition between different operational states.

**SDO (Service Data Object)**: Provides access to all device parameters and allows for reading and writing data.

**PDO (Process Data Object)**: Efficient and real-time data transfer mechanism.

**Error Handling**: Implements CANopen's error handling, including heartbeat and node guarding.

## Installation
(Here, you'd detail how one would install this library, be it through pip, manually, or any other method.)

```bash
pip install canopen-circuitpython
```


## Usage
Here's a basic example of initializing a CANopen node and sending a message:
```python
from canopen import CANopenNode, CANopenPDO

Initialize MCP2515 (this might vary based on actual setup)
mcp = adafruit_mcp2515.MCP2515(...)
node = CANopenNode(1, mcp)

Create a PDO message and send
message = CANopenPDO(0x180 + node.node_id, b'example data')
node.send(message)
```

For more examples, check the /examples directory.

## Contributing
We welcome contributions! If you'd like to contribute, please fork the repository and make changes as you'd like. Pull requests are warmly welcome.

## Issues
If you find any issues or bugs with the library, please file an issue in the repository.

## License
This project is licensed under the MIT License - see the **LICENSE** file for details.