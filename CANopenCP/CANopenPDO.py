from .CANopenMessage import CANopenMessage


class CANopenPDO:
    """Base class for CANopen PDOs."""

    # Default COB-IDs for PDOs
    COB_ID_PDO1_TX = 0x180
    COB_ID_PDO1_RX = 0x200
    COB_ID_PDO2_TX = 0x280
    COB_ID_PDO2_RX = 0x300
    COB_ID_PDO3_TX = 0x380
    COB_ID_PDO3_RX = 0x400
    COB_ID_PDO4_TX = 0x480
    COB_ID_PDO4_RX = 0x500

    def __init__(self, cob_id, data=bytes()):
        super().__init__(cob_id, data)


class CANopenTPDO(CANopenPDO):
    """CANopen Transmit PDO."""

    def __init__(self, node_id, data=bytes()):
        cob_id = self.COB_ID_PDO1_TX + node_id
        super().__init__(cob_id, data)


class CANopenRPDO(CANopenPDO):
    """CANopen Receive PDO."""

    def __init__(self, node_id, data=bytes()):
        cob_id = self.COB_ID_PDO1_RX + node_id
        super().__init__(cob_id, data)
