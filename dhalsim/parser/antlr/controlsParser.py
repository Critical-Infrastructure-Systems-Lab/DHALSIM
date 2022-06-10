# Generated from controls.g4 by ANTLR 4.7.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys

def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\27")
        buf.write(" \4\2\t\2\4\3\t\3\4\4\t\4\3\2\3\2\3\2\3\2\3\2\3\2\3\2")
        buf.write("\3\2\3\2\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\4\3\4\7\4\33\n")
        buf.write("\4\f\4\16\4\36\13\4\3\4\2\2\5\2\4\6\2\2\2\36\2\b\3\2\2")
        buf.write("\2\4\21\3\2\2\2\6\34\3\2\2\2\b\t\7\3\2\2\t\n\7\20\2\2")
        buf.write("\n\13\7\t\2\2\13\f\7\4\2\2\f\r\7\5\2\2\r\16\7\20\2\2\16")
        buf.write("\17\7\f\2\2\17\20\7\17\2\2\20\3\3\2\2\2\21\22\7\3\2\2")
        buf.write("\22\23\7\20\2\2\23\24\7\t\2\2\24\25\7\6\2\2\25\26\7\7")
        buf.write("\2\2\26\27\7\17\2\2\27\5\3\2\2\2\30\33\5\2\2\2\31\33\5")
        buf.write("\4\3\2\32\30\3\2\2\2\32\31\3\2\2\2\33\36\3\2\2\2\34\32")
        buf.write("\3\2\2\2\34\35\3\2\2\2\35\7\3\2\2\2\36\34\3\2\2\2\4\32")
        buf.write("\34")
        return buf.getvalue()


class controlsParser ( Parser ):

    grammarFileName = "controls.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'LINK'", "'IF'", "'NODE'", "'AT'", "'TIME'", 
                     "' '", "<INVALID>", "'OPEN'", "'CLOSED'", "<INVALID>", 
                     "'BELOW'", "'ABOVE'", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "'[CONTROLS]'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "SPACES", "STATE", "OPEN", 
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
    SPACES=6
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
    #PUMP_SETTING=22

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.7.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None



    class NodeControlContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(controlsParser.ID)
            else:
                return self.getToken(controlsParser.ID, i)

        def STATE(self):
            return self.getToken(controlsParser.STATE, 0)

        def CONDITION(self):
            return self.getToken(controlsParser.CONDITION, 0)

        def VALUE(self):
            return self.getToken(controlsParser.VALUE, 0)

        def getRuleIndex(self):
            return controlsParser.RULE_nodeControl




    def nodeControl(self):

        localctx = controlsParser.NodeControlContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_nodeControl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 6
            self.match(controlsParser.T__0)
            self.state = 7
            self.match(controlsParser.ID)
            self.state = 8
            self.match(controlsParser.STATE)
            self.state = 9
            self.match(controlsParser.T__1)
            self.state = 10
            self.match(controlsParser.T__2)
            self.state = 11
            self.match(controlsParser.ID)
            self.state = 12
            self.match(controlsParser.CONDITION)
            self.state = 13
            self.match(controlsParser.VALUE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class TimeControlContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(controlsParser.ID, 0)

        def STATE(self):
            return self.getToken(controlsParser.STATE, 0)

        def VALUE(self):
            return self.getToken(controlsParser.VALUE, 0)

        def getRuleIndex(self):
            return controlsParser.RULE_timeControl




    def timeControl(self):

        localctx = controlsParser.TimeControlContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_timeControl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 15
            self.match(controlsParser.T__0)
            self.state = 16
            self.match(controlsParser.ID)
            self.state = 17
            self.match(controlsParser.STATE)
            self.state = 18
            self.match(controlsParser.T__3)
            self.state = 19
            self.match(controlsParser.T__4)
            self.state = 20
            self.match(controlsParser.VALUE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class ControlsContext(ParserRuleContext):

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




    def controls(self):

        localctx = controlsParser.ControlsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_controls)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 26
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==controlsParser.T__0:
                self.state = 24
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,0,self._ctx)
                if la_ == 1:
                    self.state = 22
                    self.nodeControl()
                    pass

                elif la_ == 2:
                    self.state = 23
                    self.timeControl()
                    pass


                self.state = 28
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





