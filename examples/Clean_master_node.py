import struct
import time

import adafruit_mcp2515
import board
import busio
import digitalio

from adafruit_mcp2515 import Message
from CANopenCP.CANopenNode import CANopenMasterNode
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

def update_data(data):
    # For demonstration, we'll just increment a byte value and reset it to 0 when it reaches 256
    if data < 256:
        data += 1
    else:
        data = 0x00
    return data

if __name__ == "__main__":
    print("Initializing Master...")
    can = CANConnection()

    master = CANopenMasterNode(1, can.mcp)

    data = 0xAABBCCDD

    while True:
        # Update data in the Master node
        new_data = update_data(data)

        # Master sends a write request to the slave with the updated data
        master.send_write_request(index, subindex, new_data)

        # Master attempts to read a confirmation response from the slave
        master.read_response()

        time.sleep(5)

