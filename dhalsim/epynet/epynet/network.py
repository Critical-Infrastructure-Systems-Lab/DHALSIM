""" EPYNET Classes """
import atexit

from . import epanet2
from .objectcollection import ObjectCollection
from .node import Junction, Tank, Reservoir
from .link import Pipe, Valve, Pump
from .curve import Curve
from .pattern import Pattern
import os

class Network(object):
    """ self.epANET Network Simulation Class """
    def __init__(self, inputfile=None, units=epanet2.EN_CMH, headloss=epanet2.EN_DW, charset='UTF8'):

        # create multithreaded EPANET instance
        self.ep = epanet2.EPANET2(charset=charset)

        if inputfile:
            self.inputfile = inputfile
            self.rptfile = self.inputfile[:-3]+"rpt"
            self.binfile = self.inputfile[:-3]+"bin"
            self.ep.ENopen(self.inputfile, self.rptfile, self.binfile)
        else:
            self.inputfile = False

            self.rptfile = ""
            self.binfile = ""

            self.ep.ENinit(self.rptfile.encode(), self.binfile.encode(), units, headloss)

        self.vertices = {}
        # prepare network data
        self.nodes = ObjectCollection()
        self.junctions = ObjectCollection()
        self.reservoirs = ObjectCollection()
        self.tanks = ObjectCollection()

        self.links = ObjectCollection()
        self.pipes = ObjectCollection()
        self.valves = ObjectCollection()
        self.pumps = ObjectCollection()

        self.curves = ObjectCollection()
        self.patterns = ObjectCollection()

        self.solved = False
        self.solved_for_simtime = None

        self.load_network()

    def load_network(self):
        """ Load network data """
        # load nodes
        for index in range(1, self.ep.ENgetcount(epanet2.EN_NODECOUNT)+1):
            # get node type
            node_type = self.ep.ENgetnodetype(index)
            uid = self.ep.ENgetnodeid(index)

            if node_type == 0:
                node = Junction(uid, self)
                self.junctions[node.uid] = node
            elif node_type == 1:
                node = Reservoir(uid, self)
                self.reservoirs[node.uid] = node
                self.nodes[node.uid] = node
            else:
                node = Tank(uid, self)
                self.tanks[node.uid] = node

            self.nodes[node.uid] = node


        # load links
        for index in range(1, self.ep.ENgetcount(epanet2.EN_LINKCOUNT)+1):
            link_type = self.ep.ENgetlinktype(index)
            uid = self.ep.ENgetlinkid(index)
            # pipes
            if link_type <= 1:
                link = Pipe(uid, self)
                self.pipes[link.uid] = link
            elif link_type == 2:
                link = Pump(uid, self)
                self.pumps[link.uid] = link
            elif link_type >= 3:
                link = Valve(uid, self)
                self.valves[link.uid] = link

            self.links[link.uid] = link
            link_nodes = self.ep.ENgetlinknodes(index)
            link.from_node = self.nodes[self.ep.ENgetnodeid(link_nodes[0])]
            link.from_node.links[link.uid] = link
            link.to_node = self.nodes[self.ep.ENgetnodeid(link_nodes[1])]
            link.to_node.links[link.uid] = link


        # load curves 

        for index in range(1, self.ep.ENgetcount(epanet2.EN_CURVECOUNT)+1):
            uid = self.ep.ENgetcurveid(index)
            self.curves[uid] = Curve(uid, self)

        # load patterns
        for index in range(1, self.ep.ENgetcount(epanet2.EN_PATCOUNT)+1):
            uid = self.ep.ENgetpatternid(index)
            self.patterns[uid] = Pattern(uid, self)

    def reset(self):

        self.solved = False
        self.solved_for_simtime = None

        for link in self.links:
            link.reset()
        for node in self.nodes:
            node.reset()

    def delete_node(self, uid):
        index = self.ep.ENgetnodeindex(uid)
        node_type = self.ep.ENgetnodetype(index)

        for link in list(self.nodes[uid].links):
            self.delete_link(link.uid);

        del self.nodes[uid]

        if node_type == epanet2.EN_JUNCTION:
            del self.junctions[uid]
        elif node_type == epanet2.EN_RESERVOIR:
            del self.reservoirs[uid]
        elif node_type == epanet2.EN_TANK:
            del self.tanks[uid]

        self.ep.ENdeletenode(index)

        self.invalidate_nodes()
        self.invalidate_links()

    def delete_link(self, uid):

        index = self.ep.ENgetlinkindex(uid)
        link_type = self.ep.ENgetlinktype(index)

        link = self.links[uid]
        del link.from_node.links[uid]
        del link.to_node.links[uid]

        del self.links[uid]

        if link_type == epanet2.EN_PIPE or link_type == epanet2.EN_CVPIPE:
            del self.pipes[uid]
        elif link_type == epanet2.EN_PUMP:
            del self.pumps[uid]
        else:
            del self.valves[uid]

        self.ep.ENdeletelink(index)

        self.invalidate_nodes()
        self.invalidate_links()


    def add_reservoir(self, uid, x, y, elevation=0):

        self.ep.ENaddnode(uid, epanet2.EN_RESERVOIR)

        index = self.ep.ENgetnodeindex(uid)

        self.ep.ENsetcoord(index, x, y)

        node = Reservoir(uid, self)
        node.elevation = elevation

        self.reservoirs[uid] = node
        self.nodes[uid] = node

        self.invalidate_nodes()

        return node

    def add_junction(self, uid, x, y, basedemand=0, elevation=0):
        self.ep.ENaddnode(uid, epanet2.EN_JUNCTION)
        index = self.ep.ENgetnodeindex(uid)
        self.ep.ENsetcoord(index, x, y)
        node = Junction(uid, self)
        self.junctions[uid] = node
        self.nodes[uid] = node

        # configure node
        node.basedemand = basedemand
        node.elevation = elevation

        self.invalidate_nodes()

        return node

    def add_tank(self, uid, x, y, diameter=0, maxlevel=0, minlevel=0, tanklevel=0):
        self.ep.ENaddnode(uid, epanet2.EN_TANK)
        index = self.ep.ENgetnodeindex(uid)
        self.ep.ENsetcoord(index, x, y)
        node = Tank(uid, self)
        self.tanks[uid] = node
        self.nodes[uid] = node
        # config tank
        node.diameter = diameter
        node.maxlevel = maxlevel
        node.minlevel = minlevel
        node.tanklevel = tanklevel

        self.invalidate_nodes()

        return node

    def add_pipe(self, uid, from_node, to_node, diameter=100, length=10, roughness=0.1, check_valve=False):

        from_node = from_node if isinstance(from_node, str) else from_node.uid
        to_node = to_node if isinstance(to_node, str) else to_node.uid

        if check_valve:
            self.ep.ENaddlink(uid, epanet2.EN_CVPIPE, from_node, to_node)
        else:
            self.ep.ENaddlink(uid, epanet2.EN_PIPE, from_node, to_node)

        link = Pipe(uid, self)

        link.diameter = diameter
        link.length = length
        link.roughness = roughness

        link.from_node = self.nodes[from_node]
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.pipes[uid] = link
        self.links[uid] = link

        # set link properties
        link.diameter = diameter
        link.length = length

        self.invalidate_links()

        return link

    def add_pump(self, uid, from_node, to_node, speed=0):

        from_node = from_node if isinstance(from_node, str) else from_node.uid
        to_node = to_node if isinstance(to_node, str) else to_node.uid

        self.ep.ENaddlink(uid, epanet2.EN_PUMP, from_node, to_node)
        link = Pump(uid, self)
        link.speed = speed
        link.from_node = self.nodes[from_node]
        link.speed = speed
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.pumps[uid] = link
        self.links[uid] = link

        self.invalidate_links()

        return link

    def add_curve(self, uid, values):
        self.ep.ENaddcurve(uid)

        curve = Curve(uid, self)
        curve.values = values
        self.curves[uid] = curve

        return curve

    def add_pattern(self, uid, values):
        self.ep.ENaddpattern(uid)
        pattern = Pattern(uid, self)
        pattern.values = values
        self.patterns[uid] = pattern

        return pattern

    def add_valve(self, uid, valve_type, from_node, to_node, diameter=100, setting=0):

        from_node = from_node if isinstance(from_node, str) else from_node.uid
        to_node = to_node if isinstance(to_node, str) else to_node.uid

        if valve_type.lower() == "gpv":
            valve_type_code = epanet2.EN_GPV
        elif valve_type.lower() == "fcv":
            valve_type_code = epanet2.EN_FCV
        elif valve_type.lower() == "pbv":
            valve_type_code = epanet2.EN_PBV
        elif valve_type.lower() == "tcv":
            valve_type_code = epanet2.EN_TCV
        elif valve_type.lower() == "prv":
            valve_type_code = epanet2.EN_PRV
        elif valve_type.lower() == "psv":
            valve_type_code = epanet2.EN_PSV
        else:
            raise ValueError("Unknown Valve Type")

        self.ep.ENaddlink(uid, valve_type_code, from_node, to_node)
        link = Valve(uid, self)
        link.diameter = diameter
        link.setting = setting
        link.from_node = self.nodes[from_node]
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.valves[uid] = link
        self.links[uid] = link

        self.invalidate_links()

        return link

    def invalidate_links(self):
        # set network as unsolved
        self.solved = False
        # reset link index caches
        for link in self.links:
            link._index = None

    def invalidate_nodes(self):
        # set network as unsolved
        self.solved = False
        # reset node index caches
        for node in self.nodes:
            node._index = None

    def solve(self, simtime=0):
        """ Solve Hydraulic Network for Single Timestep"""
        if self.solved and self.solved_for_simtime == simtime:
            return

        self.reset()
        self.ep.ENsettimeparam(4, simtime)
        self.ep.ENopenH()
        self.ep.ENinitH(11)
        self.ep.ENrunH()
        self.ep.ENcloseH()
        self.solved = True
        self.solved_for_simtime = simtime

    def run(self):
        self.reset()
        self.time = []
        # open network
        self.ep.ENopenH()
        self.ep.ENinitH(11)

        simtime = 0
        timestep = 1

        self.solved = True

        while timestep > 0:
            self.ep.ENrunH()
            timestep = self.ep.ENnextH()
            self.time.append(simtime)
            self.load_attributes(simtime)
            simtime += timestep

    def load_attributes(self, simtime):
        for node in self.nodes:
            # clear cached values
            node._values = {}
            for property_name in node.properties.keys():
                if property_name not in node.results.keys():
                    node.results[property_name] = []
                node.results[property_name].append(node.get_property(node.properties[property_name]))

            # check if it's junction to add basedemand with pattern to results
            if node.node_type == 'Junction':
                if 'basedemand' not in node.results.keys():
                    node.results['basedemand'] = []
                # if pattern not set it takes the basedemand as it is
                if node.basedemand > 0 and node.pattern.uid != '1':
                    pattern_step = self.ep.ENgettimeparam(3)
                    node.results['basedemand'].append(
                        node.basedemand * node.pattern.values[(simtime // pattern_step) % len(node.pattern.values)])
                else:
                    node.results['basedemand'].append(node.basedemand)

            node.times.append(simtime)

        for link in self.links:
            # clear cached values
            link._values = {}
            for property_name in link.properties.keys():
                if property_name not in link.results.keys():
                    link.results[property_name] = []
                link.results[property_name].append(link.get_property(link.properties[property_name]))
            link.times.append(simtime)

    def save_inputfile(self, name):
        self.ep.ENsaveinpfile(name)

    def get_vertices(self, link_uid):
        if self.vertices == {}:
            self.parse_vertices()
        return self.vertices.get(link_uid, [])

    def parse_vertices(self):
        vertices = False
        if not self.inputfile or len(self.vertices) > 0:
            return

        with open(self.inputfile, 'rb') as handle:
            for line in handle.readlines():
                if b'[VERTICES]' in line:
                    vertices = True
                    continue
                elif b'[' in line:
                    vertices = False

                if b";" in line:
                    continue

                if vertices:
                    components = [c.strip() for c in line.decode(self.ep.charset).split()]
                    if len(components) < 3:
                        continue
                    if components[0] not in self.vertices:
                        self.vertices[components[0]] = []
                    self.vertices[components[0]].append((float(components[1]), float(components[2])))



    def close(self):
        print('closing')
        self.ep.ENdeleteproject()
