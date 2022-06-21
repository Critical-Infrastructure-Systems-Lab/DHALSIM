/** INP File Controls Grammar */
grammar controls;

/** Skip spaces */
//SPACES              :   ' ' -> skip;
ANY_SPACE           :   ' '+;

/** States */
STATE               :   (OPEN | CLOSED | PUMP_SETTING) ;
OPEN                :   'OPEN';
CLOSED              :   'CLOSED';
PUMP_SETTING        :   [0-9]*'.'[0-9]*;

/** Conditions */
CONDITION           :   (BELOW | ABOVE) ;
BELOW               :   'BELOW';
ABOVE               :   'ABOVE';

/** Values */
VALUE               :   [0-9]*'.'*[0-9]+ ;
ID                  :   [a-zA-Z0-9_]+ ;
CAPITALS            :   [A-Z].*? ;

/** Skip all before [CONTROLS] section */
CONTROLS_HEADER     :   '[CONTROLS]';
PRECONTORLS         :   .*?CONTROLS_HEADER -> skip;

/** Skip all other sections */
POSTCONTROLS        :   '['CAPITALS']'.*? -> skip;

/** Skip over comments */
COMMENT             :   ';'.*?NEWLINES -> skip;

/** Skip newlines, whitespaces */
NEWLINES            :   [\n]+ -> skip ;
WS                  :   [ \t\r\n]+ -> skip ;

nodeControl         :   'LINK' ANY_SPACE ID ANY_SPACE STATE ANY_SPACE 'IF' ANY_SPACE 'NODE' ANY_SPACE ID ANY_SPACE CONDITION ANY_SPACE VALUE;
timeControl         :   'LINK' ANY_SPACE ID ANY_SPACE STATE ANY_SPACE 'AT' ANY_SPACE 'TIME' ANY_SPACE VALUE;
controls            :   (nodeControl | timeControl)*;