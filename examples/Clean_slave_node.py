import struct

import adafruit_mcp2515
import board
import busio
import digitalio
import time

from adafruit_mcp2515 import Message
from CANopenCP.CANopenNode import CANopenSlaveNode
from CANopenCP import CANopenNode, CANopenClientSDO, CANopenServerSDO, CANopenSDO


class CANConnection:

    def __init__(self):
        cs = digitalio.DigitalInOut(board.CAN_CS)
        cs.switch_to_output()
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.mcp = adafruit_mcp2515.MCP2515(spi, cs, baudrate=1000000)

if __name__ == "__main__":
    print("Initializing Slave...")
    can = CANConnection()

    slave = CANopenSlaveNode(2, can.mcp)  # Assuming the node ID of the slave is 2
    slave.data_dict = {(0x1234, 0x01): bytearray(256)}

    while True:
        # Slave listens for a request and sends a response if applicable
        slave.listen_and_respond()

        time.sleep(1)