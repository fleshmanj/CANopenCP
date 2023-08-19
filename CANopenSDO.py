from .CANopenMessage import CANopenMessage


class CANopenSDO(CANopenMessage):
    """Base class for CANopen SDOs."""

    # Default COB-IDs for SDOs
    COB_ID_SDO_TX = 0x580
    COB_ID_SDO_RX = 0x600

    # SDO Command Specifier (SCS) for client requests
    SDO_DOWNLOAD_INITIATE = 0x20
    SDO_UPLOAD_INITIATE = 0x40
    SDO_DOWNLOAD_SEGMENT = 0x00
    SDO_UPLOAD_SEGMENT = 0x60
    SDO_ABORT = 0x80

    def __init__(self, cob_id, data=bytes()):
        super().__init__(cob_id, data)

    def set_data(self, command_specifier, data_bytes):
        if not isinstance(data_bytes, bytes):
            raise TypeError("data_bytes should be of type bytes")
        # Command specifier is packed as a byte 'B', and the length of data_bytes is used to generate the format
        data_format = 'B' + f'{len(data_bytes)}s'
        super().set_data(data_format, command_specifier, data_bytes)


class CANopenClientSDO(CANopenSDO):
    """CANopen Client SDO for sending requests."""

    def __init__(self, node_id, data=bytes()):
        self.id = node_id
        cob_id = self.COB_ID_SDO_RX + node_id  # Typically, client SDOs use RX base for requests.
        super().__init__(cob_id, data)
        self.extended = False  # for standard IDs


class CANopenServerSDO(CANopenSDO):
    """CANopen Server SDO for sending responses."""

    def __init__(self, node_id, data=bytes()):
        self.id = node_id
        cob_id = self.COB_ID_SDO_TX + node_id  # Typically, server SDOs use TX base for responses.
        super().__init__(cob_id, data)
