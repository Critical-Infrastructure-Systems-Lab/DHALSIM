/** INP File Controls Grammar */
grammar controls;

/** Skip spaces */
SPACES              :   ' ' -> skip;

/** States */
STATE               :   (OPEN | CLOSED) ;
OPEN                :   'OPEN';
CLOSED              :   'CLOSED';

/** Conditions */
CONDITION           :   (BELOW | ABOVE) ;
BELOW               :   'BELOW';
ABOVE               :   'ABOVE';

/** Values */
VALUE               :   [0-9]+'.'*[0-9]* ;
ID                  :   [a-zA-Z0-9_]+ ;
CAPITALS            :   [A-Z].*? ;

/** Skip all before [CONTROLS] section */
CONTROLS_HEADER     :   '[CONTROLS]';
PRECONTORLS         :   .*?CONTROLS_HEADER -> skip;

/** Skip all other sections */
POSTCONTROLS        :   '['CAPITALS']'.*? -> skip;

/** Skip over comments */
COMMENT             :   ';'.*?NEWLINES -> skip;

/** Skip newlines, whitespaces and spaces */
NEWLINES            :   [\n]+ -> skip ;
WS                  :   [ \t\r\n]+ -> skip ;

nodeControl         :   'LINK' ID STATE 'IF' 'NODE' ID CONDITION VALUE ;
timeControl         :   'LINK' ID STATE 'AT' 'TIME' VALUE ;
controls            :   (nodeControl | timeControl)*;