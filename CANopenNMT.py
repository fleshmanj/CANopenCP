class CANopenNMT:
    """CANopen Network Management."""

    # NMT Commands
    CMD_START_REMOTE_NODE = 0x01
    CMD_STOP_REMOTE_NODE = 0x02
    CMD_ENTER_PRE_OPERATIONAL = 0x80
    CMD_RESET_NODE = 0x81
    CMD_RESET_COMMUNICATION = 0x82

    # NMT States
    STATE_INITIALIZING = 0x00
    STATE_PRE_OPERATIONAL = 0x7F
    STATE_OPERATIONAL = 0x05
    STATE_STOPPED = 0x04

    def __init__(self, node_id):
        """Initialize a CANopen NMT for a specific node."""
        self.node_id = node_id
        self.current_state = CANopenNMT.STATE_INITIALIZING

    def transition(self, command):
        """Transition to a new state based on the NMT command."""

        if command == self.CMD_START_REMOTE_NODE:
            self.current_state = CANopenNMT.STATE_OPERATIONAL
        elif command == self.CMD_STOP_REMOTE_NODE:
            self.current_state = CANopenNMT.STATE_STOPPED
        elif command == self.CMD_ENTER_PRE_OPERATIONAL:
            self.current_state = CANopenNMT.STATE_PRE_OPERATIONAL
        elif command == self.CMD_RESET_NODE:
            self.current_state = CANopenNMT.STATE_INITIALIZING
        elif command == self.CMD_RESET_COMMUNICATION:
            # This would typically reset communication parameters and then move to STATE_INITIALIZING
            # but for simplicity, we just move to STATE_INITIALIZING directly
            self.current_state = CANopenNMT.STATE_INITIALIZING
        else:
            raise ValueError(f"Unknown NMT command: {command}")

    def get_state(self):
        """Return the current state of the node."""
        return self.current_state
