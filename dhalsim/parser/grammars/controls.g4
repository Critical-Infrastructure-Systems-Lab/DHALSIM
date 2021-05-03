/** INP File Controls Grammar */
grammar controls;

STATE               :   (OPEN | CLOSED) ;
OPEN                :   'OPEN';
CLOSED              :   'CLOSED';

CONDITION           :   (BELOW | ABOVE) ;
BELOW               :   'BELOW';
ABOVE               :   'ABOVE';

VALUE               :   [0-9]+'.'*[0-9]* ;
ID                  :   [a-zA-Z0-9_]+ ;
CAPITALS            :   [A-Z].*? ;

NEWLINES            :   [\n]+ -> skip ;

CONTROLS_HEADER     :   '[CONTROLS]';
PRECONTORLS         :   .*?CONTROLS_HEADER -> skip;

POSTCONTROLS        :   '['CAPITALS']'.*? -> skip;

WS                  :   [ \t\r\n]+ -> skip ;

nodeControl         :   'LINK' ID STATE 'IF NODE' ID CONDITION VALUE ;
timeControl         :   'LINK' ID STATE 'AT TIME' VALUE ;
controls            :   (nodeControl | timeControl)*;