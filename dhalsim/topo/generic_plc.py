from minicps.devices import PLC


class GenericPlc(PLC):
    """
    The BasePLC class, containing PLC functionality
    """
    def __init__(self, plc_config):
        self.plc_config = plc_config
