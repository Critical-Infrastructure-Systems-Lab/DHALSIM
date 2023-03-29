# Generated from subcatchments.g4 by ANTLR 4.9.2
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
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\r")
        buf.write("\13\4\2\t\2\3\2\3\2\3\2\3\2\3\2\3\2\3\2\2\2\3\2\2\2\2")
        buf.write("\t\2\4\3\2\2\2\4\5\7\5\2\2\5\6\7\3\2\2\6\7\7\5\2\2\7\b")
        buf.write("\7\3\2\2\b\t\7\4\2\2\t\3\3\2\2\2\2")
        return buf.getvalue()


class subcatchmentsParser ( Parser ):

    grammarFileName = "subcatchments.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "'[LOADINGS]'" ]

    symbolicNames = [ "<INVALID>", "ANY_SPACE", "VALUE", "ID", "CAPITALS", 
                      "LOADINGS_HEADER", "PRELOADINGS", "POSTLOADINGS", 
                      "COMMENT", "COMMENTSP", "NEWLINES", "WS" ]

    RULE_loading = 0

    ruleNames =  [ "loading" ]

    EOF = Token.EOF
    ANY_SPACE=1
    VALUE=2
    ID=3
    CAPITALS=4
    LOADINGS_HEADER=5
    PRELOADINGS=6
    POSTLOADINGS=7
    COMMENT=8
    COMMENTSP=9
    NEWLINES=10
    WS=11

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class LoadingContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(subcatchmentsParser.ID)
            else:
                return self.getToken(subcatchmentsParser.ID, i)

        def ANY_SPACE(self, i:int=None):
            if i is None:
                return self.getTokens(subcatchmentsParser.ANY_SPACE)
            else:
                return self.getToken(subcatchmentsParser.ANY_SPACE, i)

        def VALUE(self):
            return self.getToken(subcatchmentsParser.VALUE, 0)

        def getRuleIndex(self):
            return subcatchmentsParser.RULE_loading

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLoading" ):
                listener.enterLoading(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLoading" ):
                listener.exitLoading(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLoading" ):
                return visitor.visitLoading(self)
            else:
                return visitor.visitChildren(self)




    def loading(self):

        localctx = subcatchmentsParser.LoadingContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_loading)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 2
            self.match(subcatchmentsParser.ID)
            self.state = 3
            self.match(subcatchmentsParser.ANY_SPACE)
            self.state = 4
            self.match(subcatchmentsParser.ID)
            self.state = 5
            self.match(subcatchmentsParser.ANY_SPACE)
            self.state = 6
            self.match(subcatchmentsParser.VALUE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





