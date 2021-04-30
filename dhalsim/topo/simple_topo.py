from mininet.topo import Topo


class SimpleTopo(Topo):
    """
    This class is a mininet simple topology.
    """

    def __init__(self, plc_configs):
        """
        Initialize a simple topology

        :param plc_configs: An array of PlcConfig objects
        """
        self.plc_configs = plc_configs
        # TODO Add the plc_dicts alternative to this
        # Initialize the topology (this calls build)
        Topo.__init__(self)
