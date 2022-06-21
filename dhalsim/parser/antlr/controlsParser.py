# Generated from controls.g4 by ANTLR 4.7.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\27")
        buf.write(",\4\2\t\2\4\3\t\3\4\4\t\4\3\2\3\2\3\2\3\2\3\2\3\2\3\2")
        buf.write("\3\2\3\2\3\2\3\2\3\2\3\2\3\2\3\2\3\2\3\3\3\3\3\3\3\3\3")
        buf.write("\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\4\3\4\7\4\'\n\4\f\4\16")
        buf.write("\4*\13\4\3\4\2\2\5\2\4\6\2\2\2*\2\b\3\2\2\2\4\30\3\2\2")
        buf.write("\2\6(\3\2\2\2\b\t\7\3\2\2\t\n\7\b\2\2\n\13\7\20\2\2\13")
        buf.write("\f\7\b\2\2\f\r\7\t\2\2\r\16\7\b\2\2\16\17\7\4\2\2\17\20")
        buf.write("\7\b\2\2\20\21\7\5\2\2\21\22\7\b\2\2\22\23\7\20\2\2\23")
        buf.write("\24\7\b\2\2\24\25\7\f\2\2\25\26\7\b\2\2\26\27\7\t\2\2")
        buf.write("\27\3\3\2\2\2\30\31\7\3\2\2\31\32\7\b\2\2\32\33\7\20\2")
        buf.write("\2\33\34\7\b\2\2\34\35\7\t\2\2\35\36\7\b\2\2\36\37\7\6")
        buf.write("\2\2\37 \7\b\2\2 !\7\7\2\2!\"\7\b\2\2\"#\7\t\2\2#\5\3")
        buf.write("\2\2\2$\'\5\2\2\2%\'\5\4\3\2&$\3\2\2\2&%\3\2\2\2\'*\3")
        buf.write("\2\2\2(&\3\2\2\2()\3\2\2\2)\7\3\2\2\2*(\3\2\2\2\4&(")
        return buf.getvalue()


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
            while _la==controlsParser.T__0:
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





