import struct

import adafruit_mcp2515
from adafruit_mcp2515 import Message

from . import CANopenClientSDO, CANopenSDO, CANopenServerSDO
from .CANopenMessage import CANopenMessage
from .CANopenNMT import CANopenNMT

from .States import CANopenSDOStates as State

import adafruit_logging as logging
import asyncio

logger = logging.getLogger('test')

logger.setLevel(logging.INFO)
logger.info('Info message')
logger.error('Error message')


class CANopenNode:
    """CANopen device node."""
    BLOCK_SIZE = 4

    def __init__(self, node_id, mcp, on_transfer_complete=None):
        self.node_id = node_id
        self.mcp = mcp
        self.nmt = CANopenNMT(node_id)
        self.current_state = State.CO_SDO_ST_IDLE
        self.on_transfer_complete = on_transfer_complete

    async def send(self, message: CANopenMessage, command=None):
        mcp_message = adafruit_mcp2515.Message(message.id, message.data)
        self.mcp.send(mcp_message)

    async def initiate_block_transfer(self, direction, index, subindex, size):
        logger.info(f"Creating initiate block transfer message for {direction} direction.")
        if direction == "download":
            command = State.CO_SDO_ST_DOWNLOAD_BLK_INITIATE_REQ
        elif direction == "upload":
            command = State.CO_SDO_ST_UPLOAD_BLK_INITIATE_REQ
        else:
            raise ValueError("Invalid direction specified. Use 'download' or 'upload'.")
        message = CANopenServerSDO(self.node_id)
        message.set_data(command, struct.pack("<HBL", index, subindex, size))
        await self.send(message)
        logger.info("Initiate block transfer message sent.")

    async def send_data_block(self, index, subindex, data):
        logger.info("Sending data block.")
        try:
            segments = [data[i:i + self.BLOCK_SIZE] for i in range(0, len(data), self.BLOCK_SIZE)]
            for segment in segments:
                segment = struct.pack("<HB", index, subindex) + segment
                await self.send_segment(segment)
                if not await self.wait_for_ack():
                    raise Exception("Acknowledgment not received for segment.")
        except Exception as e:
            logger.error(f"Error sending data block: {e}")

    async def send_segment(self, segment):
        logger.info(f"Sending segment of data: {segment}")
        msg = CANopenMessage(self.node_id, segment)
        await self.send(msg, command=State.CO_SDO_ST_UPLOAD_SEGMENT_REQ)

    async def wait_for_ack(self, timeout=2.0):
        logger.info("Waiting for acknowledgment.")
        #TODO: This does not work. Need to fix.
        response = self.mcp.read_message()

        if response is None:
            logger.error("No response received.")
            return False
        command = response.data[0]

        accepted_commands = [
            State.CO_SDO_ST_DOWNLOAD_BLK_INITIATE_RSP, State.CO_SDO_ST_UPLOAD_BLK_INITIATE_RSP,
            State.CO_SDO_ST_DOWNLOAD_BLK_END_RSP, State.CO_SDO_ST_UPLOAD_BLK_END_CRSP,
            State.CO_SDO_ST_DOWNLOAD_SEGMENT_RSP, State.CO_SDO_ST_UPLOAD_SEGMENT_RSP
        ]

        if command in accepted_commands:
            return True
        else:
            return False

    async def block_transfer(self, direction, index, subindex, data):
        logger.info(f"Initiating block transfer in {direction} direction.")
        print(f"Initiating block transfer in {direction} direction.")
        await self.initiate_block_transfer(direction, index, subindex, len(data))

        if direction == "download":
            logger.info("Initiating block download.")
            await self.send_data_block(index, subindex, data)
            if not await self.wait_for_ack():
                raise ValueError("Failed to receive acknowledgment.")
            logger.info("Sending block download end request.")
            await self.send(State.CO_SDO_ST_DOWNLOAD_BLK_END_REQ)

        elif direction == "upload":
            await self.send(State.CO_SDO_ST_UPLOAD_BLK_END_SREQ)

        else:
            raise ValueError("Invalid direction specified. Use 'download' or 'upload'.")

        if self.on_transfer_complete:
            self.on_transfer_complete(direction)

    async def send_with_retry(self, message, retries=3, timeout=2.0):
        logger.info("Sending message with retry.")
        for attempt in range(retries):
            await self.send(message)
            if await self.wait_for_ack(timeout):
                return True
        raise Exception("Failed to send message after multiple retries.")

    async def receive_segment(self):
        logger.info("Receiving segment.")
        message = await self.mcp.read_message()
        if message:
            return message.data
        else:
            return None

    async def receive_data_block(self):
        logger.info("Receiving data block.")
        data = bytearray()
        while True:
            segment = await self.receive_segment()
            if segment is None:
                break
            data.extend(segment)
        return data

    async def recover_from_error(self):
        logger.info("Recovering from error.")
        await self.send(State.CO_SDO_ST_ABORT)
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
        logger.info("Listening and responding.")
        if self.state != State.CO_SDO_ST_IDLE:
            print("Node is busy or in an error state.")
            return

        message = self.mcp.read_message()
        logger.info(f"Received a message: {message.data}")
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

    def send_response(self, command, index, subindex):
        if (index, subindex) in self.data_dict:
            data = struct.pack("<HB", index, subindex)
            response = CANopenServerSDO(self.node_id)
            response.set_data(command, data)
            logger.info(f"Sending response: {response.data}")
            self.send(response)
        else:
            print("Requested data not found!")

    def send_write_ack(self, index, subindex):
        response_msg = CANopenServerSDO(self.node_id)
        response_msg.set_data(State.CO_SDO_ST_DOWNLOAD_SEGMENT_RSP, struct.pack("<HB", index, subindex))
        self.send(response_msg)
        self.state = State.CO_SDO_ST_IDLE

    def reset_state(self):
        self.state = State.CO_SDO_ST_IDLE

    def listen(self):
        logger.info("Listening.")
        while True:
            message = self.mcp.read_message()
            if message:
                logger.info(f"Received a message: MessageID: {message.id}, Message Data: {message.data}")
                try:
                    if len(message.data) > 0:
                        cmd_specifier = message.data[0]
                        if cmd_specifier == State.CO_SDO_ST_UPLOAD_INITIATE_REQ:
                            logger.info("Received upload initiate request.")
                            received_index, = struct.unpack("<H", message.data[1:3])
                            received_subindex = message.data[3]
                            self.state = State.CO_SDO_ST_UPLOAD_INITIATE_RSP
                            self.send_response(self.state, received_index, received_subindex)
                        if cmd_specifier == State.CO_SDO_ST_DOWNLOAD_INITIATE_REQ:
                            logger.info("Received download initiate request.")
                            received_index, = struct.unpack("<H", message.data[1:3])
                            received_subindex = message.data[3]
                            received_data = message.data[4:]
                            self.write_data(received_index, received_subindex, received_data)
                            self.state = State.CO_SDO_ST_DOWNLOAD_SEGMENT_RSP
                            self.send_write_ack(received_index, received_subindex)
                        if cmd_specifier == State.CO_SDO_ST_UPLOAD_SEGMENT_REQ:
                            logger.info("Received upload segment request.")
                            received_index, = struct.unpack("<H", message.data[1:3])
                            received_subindex = message.data[3]
                            self.state = State.CO_SDO_ST_UPLOAD_SEGMENT_RSP
                            self.send_response(received_index, received_subindex)
                        if cmd_specifier == State.CO_SDO_ST_DOWNLOAD_SEGMENT_REQ:
                            logger.info("Received download segment request.")
                            received_index, = struct.unpack("<H", message.data[1:3])
                            received_subindex = message.data[3]
                            received_data = message.data[4:]
                            self.write_data(received_index, received_subindex, received_data)
                            self.state = State.CO_SDO_ST_DOWNLOAD_SEGMENT_RSP
                            self.send_write_ack(received_index, received_subindex)
                        if cmd_specifier == State.CO_SDO_ST_UPLOAD_BLK_INITIATE_REQ:
                            logger.info("Received block upload initiate request.")
                            received_index, = struct.unpack("<H", message.data[1:3])
                            received_subindex = message.data[3]
                            received_size, = struct.unpack("<L", message.data[4:8])
                            self.state = State.CO_SDO_ST_UPLOAD_BLK_INITIATE_RSP
                            self.send_response(received_index, received_subindex)
                        if cmd_specifier == State.CO_SDO_ST_DOWNLOAD_BLK_INITIATE_REQ:
                            logger.info("Received block download initiate request.")
                            received_index, = struct.unpack("<H", message.data[1:3])
                            received_subindex = message.data[3]
                            received_size, = struct.unpack("<L", message.data[4:8])
                            self.state = State.CO_SDO_ST_DOWNLOAD_BLK_INITIATE_RSP
                            self.send_response(self.state, received_index, received_subindex)
                        if cmd_specifier == State.CO_SDO_ST_UPLOAD_BLK_END_SREQ:
                            logger.info("Received block upload end request.")
                            received_index, = struct.unpack("<H", message.data[1:3])
                            received_subindex = message.data[3]
                            self.state = State.CO_SDO_ST_UPLOAD_BLK_END_CRSP
                            self.send_response(received_index, received_subindex)
                        if cmd_specifier == State.CO_SDO_ST_DOWNLOAD_BLK_END_REQ:
                            logger.info("Received block download end request.")
                            received_index, = struct.unpack("<H", message.data[1:3])
                            received_subindex = message.data[3]
                            self.state = State.CO_SDO_ST_DOWNLOAD_BLK_END_RSP
                            self.send_response(received_index, received_subindex)
                        if cmd_specifier == State.CO_SDO_ST_ABORT:
                            logger.info("Received abort request.")
                            self.state = State.CO_SDO_ST_IDLE
                            self.send_response(0, 0)
                except Exception as e:
                    self.state = State.CO_SDO_ST_ABORT
                    print("Error:", e)

    def send_ack(self):
        pass
