"""Python EpanetToolkit interface

added function ENsimtime"""

import ctypes
import platform
import datetime
import os
import warnings


class EPANET2(object):

    def __init__(self, charset='UTF8'):
        _plat= platform.system()
        if _plat=='Darwin':
            dll_path = os.path.join(os.path.dirname(__file__), "lib/libepanet.dylib")
            self._lib = ctypes.cdll.LoadLibrary(dll_path)
            ctypes.c_float = ctypes.c_double
        elif _plat=='Linux':
            dll_path = os.path.join(os.path.dirname(__file__), "lib/libepanet.so")
            self._lib = ctypes.CDLL(dll_path)
            ctypes.c_float = ctypes.c_double
        elif _plat=='Windows':
          ctypes.c_float = ctypes.c_double
          try:
            # if epanet2.dll compiled with __cdecl (as in OpenWaterAnalytics)
            dll_path = os.path.join(os.path.dirname(__file__), "lib/epanet2.dll")
            self._lib = ctypes.CDLL(dll_path)
          except ValueError:
             # if epanet2.dll compiled with __stdcall (as in EPA original DLL)
             try:
               self._lib = ctypes.windll.epanet2
               self._lib.EN_getversion(self.ph, ctypes.byref(ctypes.c_int()))
             except ValueError:
               raise Exception("epanet2.dll not suitable")

        else:
          raise Exception('Platform '+ _plat +' unsupported (not yet)')


        self.charset = charset
        self._current_simulation_time=  ctypes.c_long()

        self.ph = ctypes.c_void_p()
        self._lib.EN_createproject.argtypes = [ctypes.c_void_p]
        self._lib.EN_createproject(ctypes.byref(self.ph))

        self._max_label_len= 32
        self._err_max_char= 80

    def ENepanet(self,nomeinp, nomerpt='', nomebin='', vfunc=None):
        """Runs a complete EPANET simulation.

        Arguments:
        nomeinp: name of the input file
        nomerpt: name of an output report file
        nomebin: name of an optional binary output file
        vfunc  : pointer to a user-supplied function which accepts a character string as its argument."""  
        if vfunc is not None:
            CFUNC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
            callback= CFUNC(vfunc)
        else:
            callback= None
        ierr= self._lib.EN_epanet(self.ph, ctypes.c_char_p(nomeinp.encode()), 
                            ctypes.c_char_p(nomerpt.encode()), 
                            ctypes.c_char_p(nomebin.encode()), 
                            callback)
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENopen(self, nomeinp, nomerpt='', nomebin=''):
        """Opens the Toolkit to analyze a particular distribution system

        Arguments:
        nomeinp: name of the input file
        nomerpt: name of an output report file
        nomebin: name of an optional binary output file
        """
        ierr= self._lib.EN_open(self.ph, ctypes.c_char_p(nomeinp.encode()),
                          ctypes.c_char_p(nomerpt.encode()), 
                          ctypes.c_char_p(nomebin.encode()))
        if ierr!=0: 
          raise ENtoolkitError(self, ierr)


    def ENdeleteproject(self):
      """Closes down the Toolkit system (including all files being processed)"""
      ierr= self._lib.EN_deleteproject(ctypes.byref(self.ph))
      if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENgetnodeindex(self, nodeid):
        """Retrieves the index of a node with a specified ID.

        Arguments:
        nodeid: node ID label"""
        j= ctypes.c_int()
        ierr= self._lib.EN_getnodeindex(self.ph, ctypes.c_char_p(nodeid.encode(self.charset)), ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value


    def ENgetnodeid(self, index):
        """Retrieves the ID label of a node with a specified index.

        Arguments:
        index: node index"""    
        label = ctypes.create_string_buffer(self._max_label_len)
        ierr= self._lib.EN_getnodeid(self.ph, index, ctypes.byref(label))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)


    def ENgetnodetype(self, index):
        """Retrieves the node-type code for a specific node.

        Arguments:
        index: node index"""
        j= ctypes.c_int()
        ierr= self._lib.EN_getnodetype(self.ph, index, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetcoord(self, index):
        """Retrieves the coordinates (x,y) for a specific node.

        Arguments:
        index: node index"""
        x= ctypes.c_float()
        y= ctypes.c_float()
        ierr= self._lib.EN_getcoord(self.ph, index, ctypes.byref(x), ctypes.byref(y))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return (x.value,y.value)


    def ENgetnodevalue(self, index, paramcode):
        """Retrieves the value of a specific node parameter.

        Arguments:
        index:     node index
        paramcode: Node parameter codes consist of the following constants:
                      EN_ELEVATION  Elevation
                      EN_BASEDEMAND ** Base demand
                      EN_PATTERN    ** Demand pattern index
                      EN_EMITTER    Emitter coeff.
                      EN_INITQUAL   Initial quality
                      EN_SOURCEQUAL Source quality
                      EN_SOURCEPAT  Source pattern index
                      EN_SOURCETYPE Source type (See note below)
                      EN_TANKLEVEL  Initial water level in tank
                      EN_DEMAND     * Actual demand
                      EN_HEAD       * Hydraulic head
                      EN_PRESSURE   * Pressure
                      EN_QUALITY    * Actual quality
                      EN_SOURCEMASS * Mass flow rate per minute of a chemical source
                        * computed values)
                       ** primary demand category is last on demand list

                   The following parameter codes apply only to storage tank nodes:
                      EN_INITVOLUME  Initial water volume
                      EN_MIXMODEL    Mixing model code (see below)
                      EN_MIXZONEVOL  Inlet/Outlet zone volume in a 2-compartment tank
                      EN_TANKDIAM    Tank diameter
                      EN_MINVOLUME   Minimum water volume
                      EN_VOLCURVE    Index of volume versus depth curve (0 if none assigned)
                      EN_MINLEVEL    Minimum water level
                      EN_MAXLEVEL    Maximum water level
                      EN_MIXFRACTION Fraction of total volume occupied by the inlet/outlet zone in a 2-compartment tank
                      EN_TANK_KBULK  Bulk reaction rate coefficient
                      EN_DEMANDDEFICIT Amount that full demand is reduced under PDA (read only)
                      """
        j= ctypes.c_float()
        ierr= self._lib.EN_getnodevalue(self.ph, index, paramcode, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value


    ##------
    def ENgetlinkindex(self, linkid):
        """Retrieves the index of a link with a specified ID.

        Arguments:
        linkid: link ID label"""
        j= ctypes.c_int()
        ierr= self._lib.EN_getlinkindex(self.ph, ctypes.c_char_p(linkid.encode(self.charset)), ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value


    def ENgetlinkid(self, index):
        """Retrieves the ID label of a link with a specified index.

        Arguments:
        index: link index"""
        label = ctypes.create_string_buffer(self._max_label_len)
        ierr= self._lib.EN_getlinkid(self.ph, index, ctypes.byref(label))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)


    def ENgetlinktype(self, index):
        """Retrieves the link-type code for a specific link.

        Arguments:
        index: link index"""
        j= ctypes.c_int()
        ierr= self._lib.EN_getlinktype(self.ph, index, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value


    def ENgetlinknodes(self, index):
        """Retrieves the indexes of the end nodes of a specified link.

        Arguments:
        index: link index"""
        j1= ctypes.c_int()
        j2= ctypes.c_int()
        ierr= self._lib.EN_getlinknodes(self.ph, index,ctypes.byref(j1),ctypes.byref(j2))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j1.value,j2.value

    def ENgetlinkvalue(self, index, paramcode):
        """Retrieves the value of a specific link parameter.

        Arguments:
        index:     link index
        paramcode: Link parameter codes consist of the following constants:
                     EN_DIAMETER     Diameter
                     EN_LENGTH       Length
                     EN_ROUGHNESS    Roughness coeff.
                     EN_MINORLOSS    Minor loss coeff.
                     EN_INITSTATUS   Initial link status (0 = closed, 1 = open)
                     EN_INITSETTING  Roughness for pipes, initial speed for pumps, initial setting for valves
                     EN_KBULK        Bulk reaction coeff.
                     EN_KWALL        Wall reaction coeff.
                     EN_FLOW         * Flow rate
                     EN_VELOCITY     * Flow velocity
                     EN_HEADLOSS     * Head loss
                     EN_STATUS       * Actual link status (0 = closed, 1 = open)
                     EN_SETTING      * Roughness for pipes, actual speed for pumps, actual setting for valves
                     EN_ENERGY       * Energy expended in kwatts
                       * computed values"""
        j= ctypes.c_float()
        ierr= self._lib.EN_getlinkvalue(self.ph, index, paramcode, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value
    #------

    def ENgetpatternid(self, index):
        """Retrieves the ID label of a particular time pattern.

        Arguments:
        index: pattern index"""
        label = ctypes.create_string_buffer(self._max_label_len)
        ierr= self._lib.EN_getpatternid(self.ph, index, ctypes.byref(label))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetpatternindex(self, patternid):
        """Retrieves the index of a particular time pattern.

        Arguments:
        id: pattern ID label"""
        j= ctypes.c_int()
        ierr= self._lib.EN_getpatternindex(self.ph, ctypes.c_char_p(patternid.encode(self.charset)), ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value


    def ENgetpatternlen(self, index):
        """Retrieves the number of time periods in a specific time pattern.

        Arguments:
        index:pattern index"""
        j= ctypes.c_int()
        ierr= self._lib.EN_getpatternlen(self.ph, index, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetpatternvalue(self, index, period):
        """Retrieves the multiplier factor for a specific time period in a time pattern.

        Arguments:
        index:  time pattern index
        period: period within time pattern"""
        j= ctypes.c_float()
        ierr= self._lib.EN_getpatternvalue(self.ph, index, period, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value



    def ENgetcount(self, countcode):
        """Retrieves the number of network components of a specified type.

        Arguments:
        countcode: component code EN_NODECOUNT
                                  EN_TANKCOUNT
                                  EN_LINKCOUNT
                                  EN_PATCOUNT
                                  EN_CURVECOUNT
                                  EN_CONTROLCOUNT"""
        j= ctypes.c_int()
        ierr= self._lib.EN_getcount(self.ph, countcode, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value


    def ENgetflowunits(self):
        """Retrieves a code number indicating the units used to express all flow rates."""
        j= ctypes.c_int()
        ierr= self._lib.EN_getflowunits(self.ph, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value    


    def ENgettimeparam(self, paramcode):
        """Retrieves the value of a specific analysis time parameter.
        Arguments:
        paramcode: EN_DURATION     
                   EN_HYDSTEP
                   EN_QUALSTEP
                   EN_PATTERNSTEP
                   EN_PATTERNSTART
                   EN_REPORTSTEP
                   EN_REPORTSTART
                   EN_RULESTEP
                   EN_STATISTIC
                   EN_PERIODS"""
        j= ctypes.c_int()
        ierr= self._lib.EN_gettimeparam(self.ph, paramcode, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value
        
    def  ENgetqualtype(self, qualcode):
        """Retrieves the type of water quality analysis called for
        returns  qualcode: Water quality analysis codes are as follows:
                           EN_NONE	0 No quality analysis
                           EN_CHEM	1 Chemical analysis
                           EN_AGE 	2 Water age analysis
                           EN_TRACE	3 Source tracing
                 tracenode:	index of node traced in a source tracing
                            analysis  (value will be 0 when qualcode
                            is not EN_TRACE)"""
        qualcode= ctypes.c_int()
        tracenode= ctypes.c_int()
        ierr= self._lib.EN_getqualtype(self.ph, ctypes.byref(qualcode),
                                 ctypes.byref(tracenode))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return qualcode.value, tracenode.value



    #-------Retrieving other network information--------
    def ENgetcontrol(self, cindex, ctype, lindex, setting, nindex, level ):
        """Retrieves the parameters of a simple control statement.
        Arguments:
           cindex:  control statement index
           ctype:   control type code EN_LOWLEVEL   (Low Level Control)
                                      EN_HILEVEL    (High Level Control)
                                      EN_TIMER      (Timer Control)       
                                      EN_TIMEOFDAY  (Time-of-Day Control)
           lindex:  index of link being controlled
           setting: value of the control setting
           nindex:  index of controlling node
           level:   value of controlling water level or pressure for level controls 
                    or of time of control action (in seconds) for time-based controls"""
        #int ENgetcontrol(int cindex, int* ctype, int* lindex, float* setting, int* nindex, float* level )
        ierr= self._lib.EN_getcontrol(self.ph, ctypes.c_int(cindex), ctypes.c_int(ctype), 
                                ctypes.c_int(lindex), ctypes.c_float(setting), 
                                ctypes.c_int(nindex), ctypes.c_float(level) )
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENgetoption(self, optioncode):
        """Retrieves the value of a particular analysis option.

        Arguments:
        optioncode: EN_TRIALS       
                    EN_ACCURACY 
                    EN_TOLERANCE 
                    EN_EMITEXPON 
                    EN_DEMANDMULT""" 
        j= ctypes.c_int()
        ierr= self._lib.EN_getoption(self.ph, optioncode, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetversion(self):
        """Retrieves the current version number of the Toolkit."""
        j= ctypes.c_int()
        ierr= self._lib.EN_getversion(self.ph, ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value



    #---------Setting new values for network parameters-------------
    def ENaddcontrol(self, ctype, lindex, setting, nindex, level ):
        """Sets the parameters of a simple control statement.
        Arguments:
           ctype:   control type code  EN_LOWLEVEL   (Low Level Control)
                                       EN_HILEVEL    (High Level Control)  
                                       EN_TIMER      (Timer Control)       
                                       EN_TIMEOFDAY  (Time-of-Day Control)
           lindex:  index of link being controlled
           setting: value of the control setting
           nindex:  index of controlling node
           level:   value of controlling water level or pressure for level controls
                    or of time of control action (in seconds) for time-based controls"""
        #int ENsetcontrol(int cindex, int* ctype, int* lindex, float* setting, int* nindex, float* level )
        cindex = ctypes.c_int()
        ierr= self._lib.EN_addcontrol(self.ph, ctypes.byref(cindex), ctypes.c_int(ctype),
                                ctypes.c_int(lindex), ctypes.c_float(setting), 
                                ctypes.c_int(nindex), ctypes.c_float(level))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return cindex

    def ENsetcontrol(self, cindex, ctype, lindex, setting, nindex, level ):
        """Sets the parameters of a simple control statement.
        Arguments:
           cindex:  control statement index
           ctype:   control type code  EN_LOWLEVEL   (Low Level Control)
                                       EN_HILEVEL    (High Level Control)  
                                       EN_TIMER      (Timer Control)       
                                       EN_TIMEOFDAY  (Time-of-Day Control)
           lindex:  index of link being controlled
           setting: value of the control setting
           nindex:  index of controlling node
           level:   value of controlling water level or pressure for level controls
                    or of time of control action (in seconds) for time-based controls"""
        #int ENsetcontrol(int cindex, int* ctype, int* lindex, float* setting, int* nindex, float* level )
        ierr= self._lib.EN_setcontrol(self.ph, ctypes.c_int(cindex), ctypes.c_int(ctype),
                                ctypes.c_int(lindex), ctypes.c_float(setting), 
                                ctypes.c_int(nindex), ctypes.c_float(level) )
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENsetnodevalue(self, index, paramcode, value):
        """Sets the value of a parameter for a specific node.
        Arguments:
        index:  node index
        paramcode: Node parameter codes consist of the following constants:
                      EN_ELEVATION  Elevation
                      EN_BASEDEMAND ** Base demand
                      EN_PATTERN    ** Demand pattern index
                      EN_EMITTER    Emitter coeff.
                      EN_INITQUAL   Initial quality
                      EN_SOURCEQUAL Source quality
                      EN_SOURCEPAT  Source pattern index
                      EN_SOURCETYPE Source type (See note below)
                      EN_TANKLEVEL  Initial water level in tank
                           ** primary demand category is last on demand list
                   The following parameter codes apply only to storage tank nodes
                      EN_TANKDIAM      Tank diameter
                      EN_MINVOLUME     Minimum water volume
                      EN_MINLEVEL      Minimum water level
                      EN_MAXLEVEL      Maximum water level
                      EN_MIXMODEL      Mixing model code
                      EN_MIXFRACTION   Fraction of total volume occupied by the inlet/outlet
                      EN_TANK_KBULK    Bulk reaction rate coefficient
        value:parameter value"""
        ierr= self._lib.EN_setnodevalue(self.ph, ctypes.c_int(index), ctypes.c_int(paramcode), ctypes.c_float(value))
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENsetlinkvalue(self, index, paramcode, value):
        """Sets the value of a parameter for a specific link.
        Arguments:
        index:  link index
        paramcode: Link parameter codes consist of the following constants:
                     EN_DIAMETER     Diameter
                     EN_LENGTH       Length
                     EN_ROUGHNESS    Roughness coeff.
                     EN_MINORLOSS    Minor loss coeff.
                     EN_INITSTATUS   * Initial link status (0 = closed, 1 = open)
                     EN_INITSETTING  * Roughness for pipes, initial speed for pumps, initial setting for valves
                     EN_KBULK        Bulk reaction coeff.
                     EN_KWALL        Wall reaction coeff.
                     EN_STATUS       * Actual link status (0 = closed, 1 = open)
                     EN_SETTING      * Roughness for pipes, actual speed for pumps, actual setting for valves
                     * Use EN_INITSTATUS and EN_INITSETTING to set the design value for a link's status or setting that 
                       exists prior to the start of a simulation. Use EN_STATUS and EN_SETTING to change these values while 
                       a simulation is being run (within the ENrunH - ENnextH loop).

        value:parameter value"""
        ierr= self._lib.EN_setlinkvalue(self.ph, ctypes.c_int(index), 
                                  ctypes.c_int(paramcode), 
                                  ctypes.c_float(value))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    # ---- EPYNET Extensions ---- #

    def ENinit(self, rptfile, binfile, units_code, headloss_code):
        ierr = self._lib.EN_init(self.ph, ctypes.c_char_p(rptfile), ctypes.c_char_p(binfile), ctypes.c_int(units_code), ctypes.c_int(headloss_code))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENaddnode(self, node_id, node_type_code):
        index = ctypes.c_int()

        ierr= self._lib.EN_addnode(self.ph, ctypes.c_char_p(node_id.encode(self.charset)), ctypes.c_int(node_type_code), ctypes.byref(index))
        if ierr!=0: raise ENtoolkitError(self, ierr)

        return index

    def ENdeletenode(self, node_index, conditional=0):
        ierr= self._lib.EN_deletenode(self.ph, ctypes.c_int(node_index), ctypes.c_int(conditional))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENdeletelink(self, link_index, conditional=0):
        ierr= self._lib.EN_deletelink(self.ph, ctypes.c_int(link_index), ctypes.c_int(conditional))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENaddlink(self, link_id, link_type_code, from_node_id, to_node_id):

        index = ctypes.c_int()

        ierr= self._lib.EN_addlink(self.ph, ctypes.c_char_p(link_id.encode(self.charset)), ctypes.c_int(link_type_code), ctypes.c_char_p(from_node_id.encode(self.charset)), ctypes.c_char_p(to_node_id.encode(self.charset)), ctypes.byref(index))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENsetheadcurveindex(self, pump_index, curve_index):
        ierr = self._lib.EN_setheadcurveindex(self.ph, ctypes.c_int(pump_index), ctypes.c_int(curve_index))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENgetheadcurveindex(self, pump_index):
        j= ctypes.c_int()
        ierr = self._lib.EN_getheadcurveindex(self.ph, ctypes.c_int(pump_index), ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value

    def ENaddcurve(self, curve_id):
        ierr = self._lib.EN_addcurve(self.ph, ctypes.c_char_p(curve_id.encode(self.charset)))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENsetcurvevalue(self, curve_index,point_index, x ,y):
        ierr = self._lib.EN_setcurvevalue(self.ph, ctypes.c_int(curve_index), ctypes.c_int(point_index), ctypes.c_float(x), ctypes.c_float(y))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENsetcoord(self, index, x, y):
        ierr= self._lib.EN_setcoord(self.ph, ctypes.c_int(index), 
                             ctypes.c_float(x),
                             ctypes.c_float(y))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENaddpattern(self, patternid):
        """Adds a new time pattern to the network.
        Arguments:
          id: ID label of pattern"""
        ierr= self._lib.EN_addpattern(self.ph, ctypes.c_char_p(patternid.encode(self.charset)))
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENsetpattern(self, index, factors):
        """Sets all of the multiplier factors for a specific time pattern.
        Arguments:
        index:    time pattern index
        factors:  multiplier factors list for the entire pattern"""
        # int ENsetpattern( int index, float* factors, int nfactors )
        nfactors= len(factors)
        cfactors_type= ctypes.c_float* nfactors
        cfactors= cfactors_type()
        for i in range(nfactors):
           cfactors[i]= float(factors[i] )
        ierr= self._lib.EN_setpattern(self.ph, ctypes.c_int(index), cfactors, ctypes.c_int(nfactors) )
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENsetpatternvalue(self, index, period, value):
        """Sets the multiplier factor for a specific period within a time pattern.
        Arguments:
           index: time pattern index
           period: period within time pattern
           value:  multiplier factor for the period"""
        #int ENsetpatternvalue( int index, int period, float value )
        ierr= self._lib.EN_setpatternvalue(self.ph,  ctypes.c_int(index), 
                                      ctypes.c_int(period), 
                                      ctypes.c_float(value) )
        if ierr!=0: raise ENtoolkitError(self, ierr)
     
     

    def ENsetqualtype(self, qualcode, chemname, chemunits, tracenode):
        """Sets the type of water quality analysis called for.
        Arguments:
             qualcode:	water quality analysis code
             chemname:	name of the chemical being analyzed
             chemunits:	units that the chemical is measured in
             tracenode:	ID of node traced in a source tracing analysis """
        ierr= self._lib.EN_setqualtype(self.ph,  ctypes.c_int(qualcode),
                                  ctypes.c_char_p(chemname.encode(self.charset)),
                                  ctypes.c_char_p(chemunits.encode(self.charset)),
                                  ctypes.c_char_p(tracenode.encode(self.charset)))
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def  ENsettimeparam(self, paramcode, timevalue):
        """Sets the value of a time parameter.
        Arguments:
          paramcode: time parameter code EN_DURATION
                                         EN_HYDSTEP
                                         EN_QUALSTEP
                                         EN_PATTERNSTEP
                                         EN_PATTERNSTART
                                         EN_REPORTSTEP
                                         EN_REPORTSTART
                                         EN_RULESTEP
                                         EN_STATISTIC
                                         EN_PERIODS
          timevalue: value of time parameter in seconds
                          The codes for EN_STATISTIC are:
                          EN_NONE     none
                          EN_AVERAGE  averaged
                          EN_MINIMUM  minimums
                          EN_MAXIMUM  maximums
                          EN_RANGE    ranges"""
        ierr= self._lib.EN_settimeparam(self.ph, ctypes.c_int(paramcode), ctypes.c_int(timevalue))
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENsetoption(self, optioncode, value):
        """Sets the value of a particular analysis option.

        Arguments:
          optioncode: option code EN_TRIALS
                                  EN_ACCURACY  
                                  EN_TOLERANCE 
                                  EN_EMITEXPON 
                                  EN_DEMANDMULT
          value:  option value"""
        ierr= self._lib.EN_setoption(self.ph, ctypes.c_int(optioncode), ctypes.c_float(value))
        if ierr!=0: raise ENtoolkitError(self, ierr)


    #----- Saving and using hydraulic analysis results files -------
    def ENsavehydfile(self, fname):
        """Saves the current contents of the binary hydraulics file to a file."""
        ierr= self._lib.EN_savehydfile(self.ph, ctypes.c_char_p(fname.encode()))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def  ENusehydfile(self, fname):
        """Uses the contents of the specified file as the current binary hydraulics file"""
        ierr= self._lib.EN_usehydfile(self.ph, ctypes.c_char_p(fname.encode()))
        if ierr!=0: raise ENtoolkitError(self, ierr)



    #----------Running a hydraulic analysis --------------------------
    def ENsolveH(self):
        """Runs a complete hydraulic simulation with results 
        for all time periods written to the binary Hydraulics file."""
        ierr= self._lib.EN_solveH(self.ph, )
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENopenH(self): 
        """Opens the hydraulics analysis system"""
        ierr= self._lib.EN_openH(self.ph, )


    def ENinitH(self, flag=None):
        """Initializes storage tank levels, link status and settings, 
        and the simulation clock time prior
    to running a hydraulic analysis.

        flag  EN_NOSAVE [+EN_SAVE] [+EN_INITFLOW] """
        ierr= self._lib.EN_initH(self.ph, flag)
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENrunH(self):
        """Runs a single period hydraulic analysis, 
        retrieving the current simulation clock time t"""
        ierr= self._lib.EN_runH(self.ph, ctypes.byref(self._current_simulation_time))
        if ierr>=100: 
          raise ENtoolkitError(self, ierr)
        elif ierr>0:
          warnings.warn(self.ENgeterror(ierr))
          return self.ENgeterror(ierr)

    def ENabort(self):
        self._lib.EN_abort(self.ph, )

    def ENsimtime(self):
        """retrieves the current simulation time t as datetime.timedelta instance"""
        return datetime.timedelta(seconds= self._current_simulation_time.value )

    def ENnextH(self):
        """Determines the length of time until the next hydraulic event occurs in an extended period
           simulation."""
        _deltat= ctypes.c_long()
        ierr= self._lib.EN_nextH(self.ph, ctypes.byref(_deltat))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return _deltat.value


    def ENcloseH(self):
        """Closes the hydraulic analysis system, freeing all allocated memory."""
        ierr= self._lib.EN_closeH(self.ph, )
        if ierr!=0: raise ENtoolkitError(self, ierr)

    #--------------------------------------------

    #----------Running a quality analysis --------------------------
    def ENsolveQ(self):
        """Runs a complete water quality simulation with results 
        at uniform reporting intervals written to EPANET's binary Output file."""
        ierr= self._lib.EN_solveQ(self.ph, )
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENopenQ(self):
        """Opens the water quality analysis system"""
        ierr= self._lib.EN_openQ(self.ph, )


    def ENinitQ(self, flag=None):
        """Initializes water quality and the simulation clock 
        time prior to running a water quality analysis.

        flag  EN_NOSAVE | EN_SAVE """
        ierr= self._lib.EN_initQ(self.ph, flag)
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENrunQ(self):
        """Makes available the hydraulic and water quality results
        that occur at the start of the next time period of a water quality analysis, 
        where the start of the period is returned in t."""
        ierr= self._lib.EN_runQ(self.ph, ctypes.byref(self._current_simulation_time))
        if ierr>=100: 
          raise ENtoolkitError(self, ierr)
        elif ierr>0:
          return self.ENgeterror(ierr)

    def ENnextQ(self):
        """Advances the water quality simulation 
        to the start of the next hydraulic time period."""
        _deltat= ctypes.c_long()
        ierr= self._lib.EN_nextQ(self.ph, ctypes.byref(_deltat))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return _deltat.value
        
        
    def ENstepQ(self):
        """Advances the water quality simulation one water quality time step. 
        The time remaining in the overall simulation is returned in tleft."""
        tleft= ctypes.c_long()
        ierr= self._lib.EN_nextQ(self.ph, ctypes.byref(tleft))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return tleft.value

    def ENcloseQ(self):
        """Closes the water quality analysis system, 
        freeing all allocated memory."""
        ierr= self._lib.EN_closeQ(self.ph, )
        if ierr!=0: raise ENtoolkitError(self, ierr)
    #--------------------------------------------





    def ENsaveH(self):
        """Transfers results of a hydraulic simulation 
        from the binary Hydraulics file to the binary
        Output file, where results are only reported at 
        uniform reporting intervals."""
        ierr= self._lib.EN_saveH(self.ph, )
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENsaveinpfile(self, fname):
        """Writes all current network input data to a file 
        using the format of an EPANET input file."""
        ierr= self._lib.EN_saveinpfile(self.ph,  ctypes.c_char_p(fname.encode()))
        if ierr!=0: raise ENtoolkitError(self, ierr)


    def ENreport(self):
        """Writes a formatted text report on simulation results 
        to the Report file."""
        ierr= self._lib.EN_report(self.ph, )
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENresetreport(self):
        """Clears any report formatting commands 
        
        that either appeared in the [REPORT] section of the 
        EPANET Input file or were issued with the 
        ENsetreport function"""
        ierr= self._lib.EN_resetreport(self.ph, )
        if ierr!=0: raise ENtoolkitError(self, ierr)
        
    def ENsetreport(self, command):
        """Issues a report formatting command. 
        
        Formatting commands are the same as used in the 
        [REPORT] section of the EPANET Input file."""
        ierr= self._lib.EN_setreport(self.ph, ctypes.c_char_p(command.encode(self.charset)))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENsetstatusreport(self, statuslevel):
        """Sets the level of hydraulic status reporting. 
        
        statuslevel:  level of status reporting  
                      0 - no status reporting
                      1 - normal reporting
                      2 - full status reporting"""
        ierr= self._lib.EN_setstatusreport(self.ph, ctypes.c_int(statuslevel))
        if ierr!=0: raise ENtoolkitError(self, ierr)

    def ENgeterror(self, errcode):
        """Retrieves the text of the message associated with a particular error or warning code."""
        errmsg= ctypes.create_string_buffer(self._err_max_char)
        self._lib.ENgeterror(errcode,ctypes.byref(errmsg), self._err_max_char )
        return errmsg.value.decode(self.charset)

    def ENwriteline(self, line ):
        """Writes a line of text to the EPANET report file."""
        ierr= self._lib.EN_writeline(self.ph, ctypes.c_char_p(line.encode(self.charset) ))
        if ierr!=0: raise ENtoolkitError(self, ierr)

          
          
    def ENgetcurve(self, curveIndex):
        curveid = ctypes.create_string_buffer(self._max_label_len)
        nValues = ctypes.c_int()
        xValues= (ctypes.c_float*100)()
        yValues= (ctypes.c_float*100)()
        ierr= self._lib.EN_getcurve(self.ph, curveIndex,
                              ctypes.byref(curveid),
                             ctypes.byref(nValues),
                             xValues,
                             yValues
                             )
        # strange behavior of ENgetcurve: it returns also curveID
        # better split in two distinct functions ....
        if ierr!=0: raise ENtoolkitError(self, ierr)
        curve= []
        for i in range(nValues.value):
           curve.append( (xValues[i],yValues[i]) )
        return curve

    def ENsetcurve(self, curveIndex, values):
        nValues = len(values)
        Values_type = ctypes.c_float* nValues
        xValues = Values_type()
        yValues = Values_type()
        for i in range(nValues):
            xValues[i] = float(values[i][0])
            yValues[i] = float(values[i][1])

        ierr = self._lib.EN_setcurve(self.ph, curveIndex, xValues, yValues, nValues)
        if ierr!=0: raise ENtoolkitError(self, ierr)
    

    def ENgetcurveid(self, curveIndex):
        curveid = ctypes.create_string_buffer(self._max_label_len)
        nValues = ctypes.c_int()

        xValues= (ctypes.c_float * 100)()
        yValues= (ctypes.c_float * 100)()

        ierr= self._lib.EN_getcurve(self.ph, curveIndex,
                              ctypes.byref(curveid),
                              ctypes.byref(nValues),
                              xValues,
                              yValues)
        # strange behavior of ENgetcurve: it returns also curveID
        # better split in two distinct functions ....
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return curveid.value.decode(self.charset)

    def ENgetcurveindex(self, curveId):
        j= ctypes.c_int()
        ierr= self._lib.EN_getcurveindex(self.ph, ctypes.c_char_p(curveId.encode(self.charset)), ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetcurvelen(self, curveIndex):
        j= ctypes.c_int()
        ierr= self._lib.EN_getcurvelen(self.ph, ctypes.c_int(curveIndex), ctypes.byref(j))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetcurvevalue(self, curveIndex, point):
        x = ctypes.c_float()
        y = ctypes.c_float()
        ierr= self._lib.EN_getcurvevalue(self.ph, ctypes.c_int(curveIndex), ctypes.c_int(point-1), ctypes.byref(x), ctypes.byref(y))
        if ierr!=0: raise ENtoolkitError(self, ierr)
        return x.value, y.value

    ###################################################################################################################
    ## NEW FUNCTIONS NOT FROM LIBRARY - Daveonwave
    ###################################################################################################################
    def ENdeleterule(self, rule_index):
        """
        Delete an existing rule-based control
        :param rule_index: the index of the rule to be deleted (starting from 1)
        """
        ierr = self._lib.EN_deleterule(self.ph, ctypes.c_int(rule_index))
        if ierr != 0:  raise ENtoolkitError(self, ierr)

    def ENgetruleID(self, index):
        """
        Gets the ID name of a rule-based control given its index
        :param index: the rule's index (starting from 1)
        :return: the rule's ID name.
        """
        label = ctypes.create_string_buffer(self._max_label_len)
        ierr = self._lib.EN_getruleID(self.ph, index, ctypes.byref(label))
        if ierr != 0: raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetdemandmodel(self):
        """
        Retrieves the type of demand model in use and its parameters.
        :returns dm_type: type of demand model (DDA or PDA)
                 pmin:    pressure below which there is no demand
                 preq:    pressure required to deliver full demand
                 pexp:    pressure exponent in demand function
        """
        dm_type = ctypes.c_int()
        pmin = ctypes.c_float()
        preq = ctypes.c_float()
        pexp = ctypes.c_float()
        ierr = self._lib.EN_getdemandmodel(self.ph,
                                           ctypes.byref(dm_type),
                                           ctypes.byref(pmin),
                                           ctypes.byref(preq),
                                           ctypes.byref(pexp))
        if ierr != 0: raise ENtoolkitError(self, ierr)
        return dm_type.value, pmin.value, preq.value, pexp.value

    def ENsetdemandmodel(self, dm_type, pmin, preq, pexp):
        """
        Sets the type of demand model to use and its parameters
        :param dm_type: type of demand model (DDA or PDA)
        :param pmin: pressure below which there is no demand
        :param preq: pressure required to deliver full demand
        :param pexp: pressure exponent in demand function
        """
        ierr = self._lib.EN_setdemandmodel(self.ph,
                                           ctypes.c_int(dm_type),
                                           ctypes.c_float(pmin),
                                           ctypes.c_float(preq),
                                           ctypes.c_float(pexp))
        if ierr != 0: raise ENtoolkitError(self, ierr)



EN_ELEVATION     = 0      # /* Node parameters */
EN_BASEDEMAND    = 1
EN_PATTERN       = 2
EN_EMITTER       = 3
EN_INITQUAL      = 4
EN_SOURCEQUAL    = 5
EN_SOURCEPAT     = 6
EN_SOURCETYPE    = 7
EN_TANKLEVEL     = 8
EN_DEMAND        = 9
EN_HEAD          = 10
EN_PRESSURE      = 11
EN_QUALITY       = 12
EN_SOURCEMASS    = 13
EN_INITVOLUME    = 14
EN_MIXMODEL      = 15
EN_MIXZONEVOL    = 16

EN_TANKDIAM      = 17
EN_MINVOLUME     = 18
EN_VOLCURVE      = 19
EN_MINLEVEL      = 20
EN_MAXLEVEL      = 21
EN_MIXFRACTION   = 22
EN_TANK_KBULK    = 23
EN_DEMANDDEFICIT = 27

EN_DIAMETER      = 0      # /* Link parameters */
EN_LENGTH        = 1
EN_ROUGHNESS     = 2
EN_MINORLOSS     = 3
EN_INITSTATUS    = 4
EN_INITSETTING   = 5
EN_KBULK         = 6
EN_KWALL         = 7
EN_FLOW          = 8
EN_VELOCITY      = 9
EN_HEADLOSS      = 10
EN_STATUS        = 11
EN_SETTING       = 12
EN_ENERGY        = 13

EN_DURATION      = 0      # /* Time parameters */
EN_HYDSTEP       = 1
EN_QUALSTEP      = 2
EN_PATTERNSTEP   = 3
EN_PATTERNSTART  = 4
EN_REPORTSTEP    = 5
EN_REPORTSTART   = 6
EN_RULESTEP      = 7
EN_STATISTIC     = 8
EN_PERIODS       = 9

EN_NODECOUNT     = 0      # /* Component counts */
EN_TANKCOUNT     = 1
EN_LINKCOUNT     = 2
EN_PATCOUNT      = 3
EN_CURVECOUNT    = 4
EN_CONTROLCOUNT  = 5

EN_JUNCTION      = 0      # /* Node types */
EN_RESERVOIR     = 1
EN_TANK          = 2

EN_CVPIPE        = 0      # /* Link types */
EN_PIPE          = 1
EN_PUMP          = 2
EN_PRV           = 3
EN_PSV           = 4
EN_PBV           = 5
EN_FCV           = 6
EN_TCV           = 7
EN_GPV           = 8

EN_NONE          = 0      # /* Quality analysis types */
EN_CHEM          = 1
EN_AGE           = 2
EN_TRACE         = 3

EN_CONCEN        = 0      # /* Source quality types */
EN_MASS          = 1
EN_SETPOINT      = 2
EN_FLOWPACED     = 3

EN_CFS           = 0      # /* Flow units types */
EN_GPM           = 1
EN_MGD           = 2
EN_IMGD          = 3
EN_AFD           = 4
EN_LPS           = 5
EN_LPM           = 6
EN_MLD           = 7
EN_CMH           = 8
EN_CMD           = 9

EN_HW            = 0
EN_DW            = 1
EN_CM            = 2

EN_TRIALS        = 0      # /* Misc. options */
EN_ACCURACY      = 1
EN_TOLERANCE     = 2
EN_EMITEXPON     = 3
EN_DEMANDMULT    = 4

EN_LOWLEVEL      = 0      # /* Control types */
EN_HILEVEL       = 1
EN_TIMER         = 2
EN_TIMEOFDAY     = 3

EN_AVERAGE       = 1      # /* Time statistic types.    */
EN_MINIMUM       = 2
EN_MAXIMUM       = 3
EN_RANGE         = 4

EN_MIX1          = 0      # /* Tank mixing models */
EN_MIX2          = 1
EN_FIFO          = 2
EN_LIFO          = 3

EN_NOSAVE        = 0      # /* Save-results-to-file flag */
EN_SAVE          = 1
EN_INITFLOW      = 10     # /* Re-initialize flow flag   */

EN_DDA           = 0      # /* Demand model types   */
EN_PDA           = 1



FlowUnits= { EN_CFS :"cfs"   ,
             EN_GPM :"gpm"   ,
             EN_MGD :"a-f/d" ,
             EN_IMGD:"mgd"   ,
             EN_AFD :"Imgd"  ,
             EN_LPS :"L/s"   ,
             EN_LPM :"Lpm"   ,
             EN_MLD :"m3/h"  ,
             EN_CMH :"m3/d"  ,
             EN_CMD :"ML/d"  }

class ENtoolkitError(Exception):
    def __init__(self, epanet2, ierr):
      self.warning= ierr < 100
      self.args= (ierr,)
      self.message = epanet2.ENgeterror(ierr)

      if self.message=='' and ierr!=0:
         self.message='ENtoolkit Undocumented Error '+str(ierr)+': look at text.h in epanet sources'
    def __str__(self):
      return self.message
