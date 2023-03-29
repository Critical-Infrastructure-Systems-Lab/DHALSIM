/** INP File Subcatchment Grammar */
grammar subcatchments;

/** Skip spaces */
ANY_SPACE           :   ' '+;

/** Values */
VALUE               :   [0-9]*'.'*[0-9]+;

WORDS               :   [a-z].*? ;
ID                  :   [a-zA-Z0-9_]+ ;
CAPITALS            :   [A-Z].*? ;

/** Skip all before [LOADINGS] section */
LOADINGS_HEADER     :   '[LOADINGS]';
PRELOADINGS         :   .*?LOADINGS_HEADER -> skip;

/** Skip all other sections */
POSTLOADINGS        :   '['CAPITALS']'.*? -> skip;

/** Skip over comments */
COMMENT             :   ';'.*?NEWLINES -> skip;
COMMENTSP           :   ';'.*?ANY_SPACE -> skip;

/** Skip newlines, whitespaces */
NEWLINES            :   [\n]+ -> skip ;
WS                  :   [ \t\r\n]+ -> skip ;

loading             :   ID ANY_SPACE ID ANY_SPACE VALUE;
