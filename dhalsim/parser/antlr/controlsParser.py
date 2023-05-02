# Generated from controls.g4 by ANTLR 4.12.0
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,21,42,2,0,7,0,2,1,7,1,2,2,7,2,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,
        0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,1,1,1,2,1,2,5,2,37,8,2,10,2,12,2,40,9,2,1,2,0,0,3,
        0,2,4,0,0,40,0,6,1,0,0,0,2,22,1,0,0,0,4,38,1,0,0,0,6,7,5,1,0,0,7,
        8,5,6,0,0,8,9,5,14,0,0,9,10,5,6,0,0,10,11,5,7,0,0,11,12,5,6,0,0,
        12,13,5,2,0,0,13,14,5,6,0,0,14,15,5,3,0,0,15,16,5,6,0,0,16,17,5,
        14,0,0,17,18,5,6,0,0,18,19,5,10,0,0,19,20,5,6,0,0,20,21,5,7,0,0,
        21,1,1,0,0,0,22,23,5,1,0,0,23,24,5,6,0,0,24,25,5,14,0,0,25,26,5,
        6,0,0,26,27,5,7,0,0,27,28,5,6,0,0,28,29,5,4,0,0,29,30,5,6,0,0,30,
        31,5,5,0,0,31,32,5,6,0,0,32,33,5,7,0,0,33,3,1,0,0,0,34,37,3,0,0,
        0,35,37,3,2,1,0,36,34,1,0,0,0,36,35,1,0,0,0,37,40,1,0,0,0,38,36,
        1,0,0,0,38,39,1,0,0,0,39,5,1,0,0,0,40,38,1,0,0,0,2,36,38
    ]

class controlsParser ( Parser ):

    grammarFileName = "controls.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'LINK'", "'IF'", "'NODE'", "'AT'", "'TIME'", 
                     "<INVALID>", "<INVALID>", "'OPEN'", "'CLOSED'", "<INVALID>", 
                     "'BELOW'", "'ABOVE'", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "'[CONTROLS]'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "ANY_SPACE", "STATE", "OPEN", 
                      "CLOSED", "CONDITION", "BELOW", "ABOVE", "VALUE", 
                      "ID", "CAPITALS", "CONTROLS_HEADER", "PRECONTORLS", 
                      "POSTCONTROLS", "COMMENT", "NEWLINES", "WS" ]

    RULE_nodeControl = 0
    RULE_timeControl = 1
    RULE_controls = 2

    ruleNames =  [ "nodeControl", "timeControl", "controls" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    ANY_SPACE=6
    STATE=7
    OPEN=8
    CLOSED=9
    CONDITION=10
    BELOW=11
    ABOVE=12
    VALUE=13
    ID=14
    CAPITALS=15
    CONTROLS_HEADER=16
    PRECONTORLS=17
    POSTCONTROLS=18
    COMMENT=19
    NEWLINES=20
    WS=21

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.12.0")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class NodeControlContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ANY_SPACE(self, i:int=None):
            if i is None:
                return self.getTokens(controlsParser.ANY_SPACE)
            else:
                return self.getToken(controlsParser.ANY_SPACE, i)

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(controlsParser.ID)
            else:
                return self.getToken(controlsParser.ID, i)

        def STATE(self, i:int=None):
            if i is None:
                return self.getTokens(controlsParser.STATE)
            else:
                return self.getToken(controlsParser.STATE, i)

        def CONDITION(self):
            return self.getToken(controlsParser.CONDITION, 0)

        def getRuleIndex(self):
            return controlsParser.RULE_nodeControl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNodeControl" ):
                listener.enterNodeControl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNodeControl" ):
                listener.exitNodeControl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNodeControl" ):
                return visitor.visitNodeControl(self)
            else:
                return visitor.visitChildren(self)




    def nodeControl(self):

        localctx = controlsParser.NodeControlContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_nodeControl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 6
            self.match(controlsParser.T__0)
            self.state = 7
            self.match(controlsParser.ANY_SPACE)
            self.state = 8
            self.match(controlsParser.ID)
            self.state = 9
            self.match(controlsParser.ANY_SPACE)
            self.state = 10
            self.match(controlsParser.STATE)
            self.state = 11
            self.match(controlsParser.ANY_SPACE)
            self.state = 12
            self.match(controlsParser.T__1)
            self.state = 13
            self.match(controlsParser.ANY_SPACE)
            self.state = 14
            self.match(controlsParser.T__2)
            self.state = 15
            self.match(controlsParser.ANY_SPACE)
            self.state = 16
            self.match(controlsParser.ID)
            self.state = 17
            self.match(controlsParser.ANY_SPACE)
            self.state = 18
            self.match(controlsParser.CONDITION)
            self.state = 19
            self.match(controlsParser.ANY_SPACE)
            self.state = 20
            self.match(controlsParser.STATE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TimeControlContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ANY_SPACE(self, i:int=None):
            if i is None:
                return self.getTokens(controlsParser.ANY_SPACE)
            else:
                return self.getToken(controlsParser.ANY_SPACE, i)

        def ID(self):
            return self.getToken(controlsParser.ID, 0)

        def STATE(self, i:int=None):
            if i is None:
                return self.getTokens(controlsParser.STATE)
            else:
                return self.getToken(controlsParser.STATE, i)

        def getRuleIndex(self):
            return controlsParser.RULE_timeControl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTimeControl" ):
                listener.enterTimeControl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTimeControl" ):
                listener.exitTimeControl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTimeControl" ):
                return visitor.visitTimeControl(self)
            else:
                return visitor.visitChildren(self)




    def timeControl(self):

        localctx = controlsParser.TimeControlContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_timeControl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 22
            self.match(controlsParser.T__0)
            self.state = 23
            self.match(controlsParser.ANY_SPACE)
            self.state = 24
            self.match(controlsParser.ID)
            self.state = 25
            self.match(controlsParser.ANY_SPACE)
            self.state = 26
            self.match(controlsParser.STATE)
            self.state = 27
            self.match(controlsParser.ANY_SPACE)
            self.state = 28
            self.match(controlsParser.T__3)
            self.state = 29
            self.match(controlsParser.ANY_SPACE)
            self.state = 30
            self.match(controlsParser.T__4)
            self.state = 31
            self.match(controlsParser.ANY_SPACE)
            self.state = 32
            self.match(controlsParser.STATE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ControlsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def nodeControl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(controlsParser.NodeControlContext)
            else:
                return self.getTypedRuleContext(controlsParser.NodeControlContext,i)


        def timeControl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(controlsParser.TimeControlContext)
            else:
                return self.getTypedRuleContext(controlsParser.TimeControlContext,i)


        def getRuleIndex(self):
            return controlsParser.RULE_controls

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterControls" ):
                listener.enterControls(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitControls" ):
                listener.exitControls(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitControls" ):
                return visitor.visitControls(self)
            else:
                return visitor.visitChildren(self)




    def controls(self):

        localctx = controlsParser.ControlsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_controls)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 38
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==1:
                self.state = 36
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,0,self._ctx)
                if la_ == 1:
                    self.state = 34
                    self.nodeControl()
                    pass

                elif la_ == 2:
                    self.state = 35
                    self.timeControl()
                    pass


                self.state = 40
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





