import adafruit_mcp2515
from .CANopenMessage import CANopenMessage
from .CANopenNMT import CANopenNMT


class CANopenNode:
    """CANopen device node."""

    def __init__(self, node_id, mcp):
        self.node_id = node_id
        self.mcp = mcp
        self.nmt = CANopenNMT(node_id)

    def send(self, message: CANopenMessage):
        mcp_message = adafruit_mcp2515.Message(message.id, message.data)
        self.mcp.send(mcp_message)

    # ... Other CANopen features ...
