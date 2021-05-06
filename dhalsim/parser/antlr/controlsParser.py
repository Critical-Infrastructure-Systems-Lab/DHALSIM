# Generated from /Users/maarten/Documents/GitLab/dhalsim/dhalsim/parser/grammars/controls.g4 by ANTLR 4.9.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\24")
        buf.write("\36\4\2\t\2\4\3\t\3\4\4\t\4\3\2\3\2\3\2\3\2\3\2\3\2\3")
        buf.write("\2\3\2\3\3\3\3\3\3\3\3\3\3\3\3\3\4\3\4\7\4\31\n\4\f\4")
        buf.write("\16\4\34\13\4\3\4\2\2\5\2\4\6\2\2\2\34\2\b\3\2\2\2\4\20")
        buf.write("\3\2\2\2\6\32\3\2\2\2\b\t\7\3\2\2\t\n\7\r\2\2\n\13\7\6")
        buf.write("\2\2\13\f\7\4\2\2\f\r\7\r\2\2\r\16\7\t\2\2\16\17\7\f\2")
        buf.write("\2\17\3\3\2\2\2\20\21\7\3\2\2\21\22\7\r\2\2\22\23\7\6")
        buf.write("\2\2\23\24\7\5\2\2\24\25\7\f\2\2\25\5\3\2\2\2\26\31\5")
        buf.write("\2\2\2\27\31\5\4\3\2\30\26\3\2\2\2\30\27\3\2\2\2\31\34")
        buf.write("\3\2\2\2\32\30\3\2\2\2\32\33\3\2\2\2\33\7\3\2\2\2\34\32")
        buf.write("\3\2\2\2\4\30\32")
        return buf.getvalue()


class controlsParser ( Parser ):

    grammarFileName = "controls.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'LINK'", "'IF NODE'", "'AT TIME'", "<INVALID>", 
                     "'OPEN'", "'CLOSED'", "<INVALID>", "'BELOW'", "'ABOVE'", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "'[CONTROLS]'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "STATE", "OPEN", "CLOSED", "CONDITION", "BELOW", "ABOVE", 
                      "VALUE", "ID", "CAPITALS", "CONTROLS_HEADER", "PRECONTORLS", 
                      "POSTCONTROLS", "COMMENT", "NEWLINES", "WS" ]

    RULE_nodeControl = 0
    RULE_timeControl = 1
    RULE_controls = 2

    ruleNames =  [ "nodeControl", "timeControl", "controls" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    STATE=4
    OPEN=5
    CLOSED=6
    CONDITION=7
    BELOW=8
    ABOVE=9
    VALUE=10
    ID=11
    CAPITALS=12
    CONTROLS_HEADER=13
    PRECONTORLS=14
    POSTCONTROLS=15
    COMMENT=16
    NEWLINES=17
    WS=18

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class NodeControlContext(ParserRuleContext):
        __slots__ = 'parser'

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
            self.match(controlsParser.ID)
            self.state = 8
            self.match(controlsParser.STATE)
            self.state = 9
            self.match(controlsParser.T__1)
            self.state = 10
            self.match(controlsParser.ID)
            self.state = 11
            self.match(controlsParser.CONDITION)
            self.state = 12
            self.match(controlsParser.VALUE)
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

        def ID(self):
            return self.getToken(controlsParser.ID, 0)

        def STATE(self):
            return self.getToken(controlsParser.STATE, 0)

        def VALUE(self):
            return self.getToken(controlsParser.VALUE, 0)

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
            self.state = 14
            self.match(controlsParser.T__0)
            self.state = 15
            self.match(controlsParser.ID)
            self.state = 16
            self.match(controlsParser.STATE)
            self.state = 17
            self.match(controlsParser.T__2)
            self.state = 18
            self.match(controlsParser.VALUE)
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
            self.state = 24
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==controlsParser.T__0:
                self.state = 22
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,0,self._ctx)
                if la_ == 1:
                    self.state = 20
                    self.nodeControl()
                    pass

                elif la_ == 2:
                    self.state = 21
                    self.timeControl()
                    pass


                self.state = 26
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





