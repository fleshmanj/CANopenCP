import struct

import adafruit_mcp2515
from adafruit_mcp2515 import Message

from . import CANopenClientSDO, CANopenSDO, CANopenServerSDO
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


class CANopenMasterNode(CANopenNode):
    def __init__(self, node_id, mcp):
        super().__init__(node_id, mcp)
        self.mcp = mcp  # MCP2515 or any other CAN controller

    def send_read_request(self, index, subindex):
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

    def send_write_request(self, index, subindex, data_to_write):
        try:
            # Constructing an SDO request to write data to the slave
            request_msg = CANopenClientSDO(self.node_id)

            # Using the DOWNLOAD_INITIATE command specifier and packing the index, subindex, and data
            request_msg.set_data(CANopenSDO.SDO_DOWNLOAD_INITIATE, struct.pack("<HBB", index, subindex, data_to_write))

            print("Sending write request...")
            print("Request msg ID:", request_msg.id)
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

class CANopenSlaveNode(CANopenNode):

    def __init__(self, node_id, mcp):
        super().__init__(node_id, mcp)
        self.node_id = node_id
        self.mcp = mcp
        # The dictionary represents the data on the Slave.
        # The key is a tuple of (index, subindex) and the value is the data.
        self.data_dict = {}

    def write_data(self, index, subindex, data):
        """Writes data to the node's dictionary at the given index and subindex."""
        self.data_dict[(index, subindex)] = data

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
                if cmd_specifier == CANopenSDO.SDO_DOWNLOAD_INITIATE:
                    print("Command matches SDO_DOWNLOAD_INITIATE. Attempting to unpack remaining data...")
                    # Bytes 1-2: Index
                    received_index, = struct.unpack("<H", message.data[1:3])

                    # Byte 3: Subindex
                    received_subindex = message.data[3]

                    # Following bytes: Data
                    received_data = message.data[4:]
                    received_data_as_bytes = bytes(received_data)  # Convert bytearray to bytes

                    print(
                        f"Received Index: {received_index}, Subindex: {received_subindex}, Data: {received_data_as_bytes}")
                    try:
                        self.write_data(received_index, received_subindex, received_data_as_bytes)

                        print("Data written successfully!")
                        print("Data written:", self.data_dict[(received_index, received_subindex)])
                        # Now, if you want to respond back, you should send the received data or an acknowledgment.
                        # Just be sure to use received_data_as_bytes (which is of type bytes) and not received_data (which is a bytearray).

                        response_msg = CANopenServerSDO(self.node_id)

                        # Using the DOWNLOAD_RESPONSE command specifier and packing the index and subindex.
                        # No data is added in this example for simplicity, but you can adjust as needed.
                        response_msg.set_data(CANopenSDO.SDO_DOWNLOAD_SEGMENT, struct.pack("<HB", received_index, received_subindex))

                        print("Sending write response...")
                        print("Response msg ID:", response_msg.id)
                        print("Response msg data:", response_msg.data)
                        self.mcp.send(response_msg)
                    except Exception as e:
                        print("Error writing data:", e)



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