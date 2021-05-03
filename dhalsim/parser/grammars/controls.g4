/** INP File Controls Grammar */
grammar controls;

WS          :   [ \t\r\n]+ -> skip ; // skip spaces, tabs, newlines
STATE       :   (OPEN | CLOSED) ;
OPEN        :   'OPEN';
CLOSED      :   'CLOSED';
CONDITION   :   (BELOW | ABOVE) ;
BELOW       :   'BELOW';
ABOVE       :   'ABOVE';
VALUE       :   [0-9]+'.'*[0-9]* ;
ID          :   [a-zA-Z0-9]+ ;

nodeControl :   'LINK' ID STATE 'IF NODE' ID CONDITION VALUE ;
timeControl :   'LINK' ID STATE 'AT TIME' VALUE ;