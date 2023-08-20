import struct

import adafruit_mcp2515
from adafruit_mcp2515 import Message

from . import CANopenClientSDO, CANopenSDO, CANopenServerSDO
from .CANopenMessage import CANopenMessage
from .CANopenNMT import CANopenNMT
from States import CANopenSDOStates as State

import logging
logger = logging.getLogger(__name__)


class CANopenNode:
    """CANopen device node."""
    BLOCK_SIZE = 256

    def __init__(self, node_id, mcp, on_transfer_complete=None):
        self.node_id = node_id
        self.mcp = mcp
        self.nmt = CANopenNMT(node_id)
        self.current_state = State.CO_SDO_ST_IDLE
        self.on_transfer_complete = on_transfer_complete

    def send(self, message: CANopenMessage):
        mcp_message = adafruit_mcp2515.Message(message.id, message.data)
        self.mcp.send(mcp_message)

    def initiate_block_transfer(self, direction, size):
        """
        Initiates a block transfer.

        :param direction: "download" or "upload"
        :param size: The size of the data to be transferred.
        """
        # Send the initiation command
        if direction == "download":
            command = State.CO_SDO_ST_DOWNLOAD_BLK_INITIATE_REQ
        elif direction == "upload":
            command = State.CO_SDO_ST_UPLOAD_BLK_INITIATE_REQ
        else:
            raise ValueError("Invalid direction specified. Use 'download' or 'upload'.")

        message = struct.pack("<B", command.value)  # Get the actual value of the enum
        self.mcp.send(message)  # This assumes you have an mcp attribute in your class that handles sending messages

    def send_data_block(self, data):
        """
        Sends a block of data.

        :param data: The block of data to be sent.
        """
        try:
            # Segment the data if needed and send it
            segments = [data[i:i + self.BLOCK_SIZE] for i in range(0, len(data), self.BLOCK_SIZE)]

            for segment in segments:
                # Send each segment
                self.send_segment(segment)
                if not self.wait_for_ack():
                    raise Exception("Acknowledgment not received for segment.")
        except Exception as e:
            logger.error(f"Error sending data block: {e}")

    def send_segment(self, segment):
        """Sends a single segment of data."""
        # For simplicity, we assume segment is just being directly sent
        # You might need to prepend/append headers, footers or other protocol specifics
        self.mcp.send(segment, command=State.CO_SDO_ST_UPLOAD_SEGMENT_REQ.value)

    def wait_for_ack(self, timeout=2.0):
        """Waits for an acknowledgment from the server."""
        response = self.mcp.read_message()

        # Check the response for acknowledgment (modify as per actual protocol)
        if response == State.CO_SDO_ST_UPLOAD_SEGMENT_RSP.value:
            return True
        else:
            return False

    def block_transfer(self, direction, data):
        """
        Conducts a block transfer.

        :param direction: "download" or "upload"
        :param data: The data to be transferred in case of download.
        """
        self.initiate_block_transfer(direction, len(data))

        if direction == "download":
            self.send_data_block(data)
            if not self.wait_for_ack():
                raise ValueError("Failed to receive acknowledgment.")
            self.mcp.send(State.CO_SDO_ST_DOWNLOAD_BLK_END_REQ.value)

        elif direction == "upload":
            # Implement block upload mechanism here
            self.mcp.send(State.CO_SDO_ST_UPLOAD_BLK_END_SREQ.value)

        else:
            raise ValueError("Invalid direction specified. Use 'download' or 'upload'.")

        # After successfully completing the transfer
        if self.on_transfer_complete:
            self.on_transfer_complete(direction)

    def send_with_retry(self, message, retries=3, timeout=2.0):
        for attempt in range(retries):
            self.mcp.send(message)
            if self.wait_for_ack(timeout):
                return True
            # Log the failed attempt or sleep for a short duration before retrying
        raise Exception("Failed to send message after multiple retries.")

    def receive_segment(self):
        """Receives a single segment of data."""
        message = self.mcp.read_message()
        if message:
            # parse the message and return the data
            return message.data
        else:
            return None


    def receive_data_block(self):
        data = bytearray()
        while True:
            segment = self.receive_segment()
            if segment is None:
                break
            data.extend(segment)
        return data

    def recover_from_error(self):
        """
        Send a reset or abort command, reset internal states, etc. to recover from an error.
        :return:
        """
        self.mcp.send(State.CO_SDO_ST_ABORT.value)
        self.current_state = State.CO_SDO_ST_IDLE



# ... Other CANopen features ...


class CANopenMasterNode(CANopenNode):
    def __init__(self, node_id, mcp):
        super().__init__(node_id, mcp)
        self.state = State.CO_SDO_ST_IDLE

    def send_read_request(self, index, subindex):
        if self.state != State.CO_SDO_ST_IDLE:
            raise Exception("Node is busy or in error state.")

        try:
            # Constructing an SDO request to fetch some parameter
            request_msg = CANopenClientSDO(self.node_id)
            request_msg.set_data(CANopenSDO.SDO_UPLOAD_INITIATE, struct.pack("<HB", index, subindex))
            self.send(request_msg)
            self.state = State.CO_SDO_ST_UPLOAD_INITIATE_REQ
        except Exception as e:
            self.state = State.CO_SDO_ST_ABORT
            raise e

    def send_write_request(self, index, subindex, data_to_write):
        if self.state != State.CO_SDO_ST_IDLE:
            raise Exception("Node is busy or in error state.")

        try:
            # Constructing an SDO request to write data to the slave
            request_msg = CANopenClientSDO(self.node_id)
            request_msg.set_data(CANopenSDO.SDO_DOWNLOAD_INITIATE, struct.pack("<HBB", index, subindex, data_to_write))
            self.send(request_msg)
            self.state = State.CO_SDO_ST_DOWNLOAD_INITIATE_REQ
        except Exception as e:
            self.state = State.CO_SDO_ST_ABORT
            raise e

    def read_response(self):
        if self.state not in [State.CO_SDO_ST_UPLOAD_INITIATE_REQ, State.CO_SDO_ST_DOWNLOAD_INITIATE_REQ]:
            raise Exception("Not expecting a response currently.")

        try:
            # Read the next available message from the bus
            response = self.mcp.read_message()

            if isinstance(response, Message):  # Assuming Message is an expected type
                decoded_index, decoded_subindex = struct.unpack("<HB", response.data[:3])
                if self.state == State.CO_SDO_ST_UPLOAD_INITIATE_REQ:
                    self.state = State.CO_SDO_ST_UPLOAD_INITIATE_RSP
                else:
                    self.state = State.CO_SDO_ST_DOWNLOAD_INITIATE_RSP
                return decoded_index, decoded_subindex
            else:
                self.state = State.CO_SDO_ST_ABORT
                raise ValueError("Received message is not of the expected type.")
        except Exception as e:
            self.state = State.CO_SDO_ST_ABORT
            raise e

    def reset_state(self):
        self.state = State.CO_SDO_ST_IDLE

class CANopenSlaveNode(CANopenNode):

    def __init__(self, node_id, mcp):
        super().__init__(node_id, mcp)
        # The dictionary represents the data on the Slave.
        # The key is a tuple of (index, subindex) and the value is the data.
        self.data_dict = {}
        self.state = State.CO_SDO_ST_IDLE

    def write_data(self, index, subindex, data):
        """Writes data to the node's dictionary at the given index and subindex."""
        self.data_dict[(index, subindex)] = data

    def listen_and_respond(self):
        if self.state != State.CO_SDO_ST_IDLE:
            print("Node is busy or in an error state.")
            return

        message = self.mcp.read_message()
        if message:
            try:
                cmd_specifier = message.data[0]
                if cmd_specifier == CANopenSDO.SDO_UPLOAD_INITIATE:
                    received_index, = struct.unpack("<H", message.data[1:3])
                    received_subindex = message.data[3]
                    self.state = State.CO_SDO_ST_UPLOAD_INITIATE_RSP
                    self.send_response(received_index, received_subindex)
                elif cmd_specifier == CANopenSDO.SDO_DOWNLOAD_INITIATE:
                    received_index, = struct.unpack("<H", message.data[1:3])
                    received_subindex = message.data[3]
                    received_data = message.data[4:]
                    self.write_data(received_index, received_subindex, received_data)
                    self.state = State.CO_SDO_ST_DOWNLOAD_SEGMENT_RSP
                    self.send_write_ack(received_index, received_subindex)
            except Exception as e:
                self.state = State.CO_SDO_ST_ABORT
                print("Error:", e)

    def send_response(self, index, subindex):
        if (index, subindex) in self.data_dict:
            data = self.data_dict[(index, subindex)]
            response = CANopenServerSDO(self.node_id)
            response.set_data(State.CO_SDO_ST_UPLOAD_SEGMENT_RSP, data)
            self.mcp.send(response)
            self.state = State.CO_SDO_ST_IDLE
        else:
            print("Requested data not found!")

    def send_write_ack(self, index, subindex):
        response_msg = CANopenServerSDO(self.node_id)
        response_msg.set_data(State.CO_SDO_ST_DOWNLOAD_SEGMENT_RSP, struct.pack("<HB", index, subindex))
        self.mcp.send(response_msg)
        self.state = State.CO_SDO_ST_IDLE

    def reset_state(self):
        self.state = State.CO_SDO_ST_IDLE

