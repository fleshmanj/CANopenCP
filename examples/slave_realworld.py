import struct

import adafruit_mcp2515
import board
import busio
import digitalio
import time

from adafruit_mcp2515 import Message
from CANopenCP import CANopenNode, CANopenClientSDO, CANopenServerSDO, CANopenSDO

# Index and subindex for the parameter you want
index = 0x1234  # example value
subindex = 0x01  # example value

class CANMessage:
    def __init__(self, id, data):
        self.id = id
        self.data = data
        self.extended = False

def sdo_to_can_message(sdo_msg):
    return CANMessage(sdo_msg.id, sdo_msg.data)


class CANConnection:

    def __init__(self):
        cs = digitalio.DigitalInOut(board.CAN_CS)
        cs.switch_to_output()
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.mcp = adafruit_mcp2515.MCP2515(spi, cs, baudrate=1000000)


class DummySlaveNode(CANopenNode):

    def __init__(self, node_id, mcp):
        self.node_id = node_id
        self.mcp = mcp
        # The dictionary represents the data on the Slave.
        # The key is a tuple of (index, subindex) and the value is the data.
        self.data_dict = {(0x1234, 0x01): struct.pack("<I", 0xAABBCCDD)}

    def listen_and_respond(self):
        message = self.mcp.read_message()
        if message:
            print("Received a message:", message.data)
            print("Length of received data:", len(message.data))
            try:
                # Check the first byte (command specifier) without unpacking the rest
                cmd_specifier = message.data[0]
                print(f"Command specifier: {cmd_specifier}")
                if cmd_specifier == CANopenSDO.SDO_UPLOAD_INITIATE:
                    print("Command matches SDO_UPLOAD_INITIATE. Attempting to unpack remaining data...")
                    # Bytes 1-2: Index
                    received_index, = struct.unpack("<H", message.data[1:3])

                    # Byte 3: Subindex
                    received_subindex = message.data[3]

                    print(f"Received Index: {received_index}, Subindex: {received_subindex}")
                    # Construct a response
                    self.send_response(received_index, received_subindex)
            except Exception as e:
                print("Error parsing received message:", e)

    def send_response(self, index, subindex):
        if (index, subindex) in self.data_dict:
            data = self.data_dict[(index, subindex)]
            # Prepare the response message
            response = CANopenServerSDO(self.node_id)
            response.set_data(CANopenSDO.SDO_UPLOAD_INITIATE, data)
            print("Sending response:", response.data)
            self.mcp.send(response)
        else:
            print("Requested data not found!")

if __name__ == "__main__":
    print("Initializing Slave...")
    can = CANConnection()

    slave = DummySlaveNode(2, can.mcp)  # Assuming the node ID of the slave is 2

    while True:
        # Slave listens for a request and sends a response if applicable
        slave.listen_and_respond()

        time.sleep(1)