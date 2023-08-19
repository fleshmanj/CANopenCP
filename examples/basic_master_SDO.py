import struct
import time

import adafruit_mcp2515
import board
import busio
import digitalio

from adafruit_mcp2515 import Message
from CANopenCP import CANopenNode, CANopenClientSDO, CANopenServerSDO, CANopenSDO

index = 0x1234  # example value
subindex = 0x01  # example value


class CANConnection:
    def __init__(self):
        # Initialize the chip select for MCP2515
        cs = digitalio.DigitalInOut(board.CAN_CS)
        cs.switch_to_output()

        # Initialize the SPI bus
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        while not spi.try_lock():
            pass
        spi.configure(baudrate=1000000)
        spi.unlock()

        self.mcp = adafruit_mcp2515.MCP2515(spi, cs, baudrate=1000000)


class SimpleMasterNode(CANopenNode):
    def __init__(self, node_id, mcp):
        super().__init__(node_id, mcp)
        self.mcp = mcp  # MCP2515 or any other CAN controller

    def send_request(self):
        try:
            # Constructing an SDO request to fetch some parameter
            request_msg = CANopenClientSDO(self.node_id)
            request_msg.set_data(CANopenSDO.SDO_UPLOAD_INITIATE, struct.pack("<HB", index, subindex))
            print("Sending request...")
            print("Request msg ID:", request_msg.id)
            print("Request msg extended:", request_msg.extended)
            print("Request msg data:", request_msg.data)
            self.mcp.send(request_msg)
        except Exception as e:
            print("Error sending message:", e)

    def read_response(self):
        try:
            # Read the next available message from the bus
            response = self.mcp.read_message()
            print("Raw received message ID:", response.id)
            print("Raw received message data:", response.data)
            print("type of message:", type(response))

            if isinstance(response, Message):
                decoded_index, decoded_subindex = struct.unpack("<HB", response.data[:3])
                print(f"Decoded Index: {decoded_index}, Subindex: {decoded_subindex}")
            else:
                print("Received message is not a CANopenServerSDO.")
        except Exception as e:
            print("Error reading message:", e)


if __name__ == "__main__":
    print("Initializing Master...")
    can = CANConnection()

    master = SimpleMasterNode(1, can.mcp)

    while True:
        # Master sends a request to the slave
        master.send_request()

        # Master attempts to read a response
        master.read_response()

        time.sleep(1)
