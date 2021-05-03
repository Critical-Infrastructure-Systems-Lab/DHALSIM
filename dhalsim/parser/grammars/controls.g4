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
NEWLINES            :   [\n]+ -> skip ;

CONTROLS_HEADER     :   '[CONTROLS]';
PRECONTORLS         :   .*CONTROLS_HEADER -> skip;

CAPITALS            :   [A-Z]* ;

WS                  :   [ \t\r\n]+ -> skip ; // skip spaces, tabs, newlines

nodeControl         :   'LINK' ID STATE 'IF NODE' ID CONDITION VALUE ;
timeControl         :   'LINK' ID STATE 'AT TIME' VALUE ;
controls            :   (nodeControl | timeControl)*;