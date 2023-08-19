import struct
from adafruit_mcp2515 import Message

class CANopenMessage(Message):
    """Base class for CANopen messages."""

    # Default COB-IDs (Communication Object Identifiers)
    COB_ID_NMT = 0x000
    COB_ID_SYNC = 0x080
    COB_ID_EMCY = 0x080
    COB_ID_TIME = 0x100
    COB_ID_PDO1_TX = 0x180
    COB_ID_PDO1_RX = 0x200
    COB_ID_PDO2_TX = 0x280
    COB_ID_PDO2_RX = 0x300
    COB_ID_PDO3_TX = 0x380
    COB_ID_PDO3_RX = 0x400
    COB_ID_PDO4_TX = 0x480
    COB_ID_PDO4_RX = 0x500
    COB_ID_SDO_TX = 0x580
    COB_ID_SDO_RX = 0x600
    COB_ID_HEARTBEAT = 0x700

    def __init__(self, cob_id, data=bytes(), extended=False):
        """Initialize a CANopen message."""
        super().__init__(cob_id, data)  # Use the COB_ID as the CAN ID.
        self.extended = extended  # Allows setting extended IDs if needed.
        self.cob_id = cob_id
        self.data = data

    def set_data(self, data_format, *values):
        """
        Set the data for the message based on a format string and values.

        :param data_format: A format string as used by the struct module to pack the data.
        :param values: Values to pack into the message data.
        """
        self.data = struct.pack(data_format, *values)

    def get_data(self, data_format):
        """
        Unpack the message data based on a format string.

        :param data_format: A format string as used by the struct module to unpack the data.
        :return: Unpacked values.
        """
        return struct.unpack(data_format, self.data)
