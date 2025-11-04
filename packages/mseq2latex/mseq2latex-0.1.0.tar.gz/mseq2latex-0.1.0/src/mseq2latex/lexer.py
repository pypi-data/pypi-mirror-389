import ply.lex as lex

# 定义标记
tokens = (
    'LBRACE',          # {
    'RBRACE',          # }
    'EQ',              # EQ
    'CMD_FRACTION',    # \f
    'CMD_RADICAL',     # \r
    'CMD_BRACKET',     # \b
    'CMD_DISPLACE',    # \d
    'CMD_INTEGRAL',    # \i
    'CMD_LIST',        # \l
    'CMD_OVERSTRIKE',  # \o
    'CMD_BOX',         # \x
    'CMD_ARRAY',       # \a
    'CMD_SUP',         # \s\up 或 \s\up数字
    'CMD_SUB',         # \s\do 或 \s\do数字
    'CMD_ALIGN_INC',   # \s\ai 或 \s\ai数字
    'CMD_ALIGN_DEC',   # \s\di 或 \s\di数字
    'BRACKET_OPTION',  # \lc\字符、\rc\字符、\bc\字符
    'DISPLACE_OPTION', # \fon、\ba、\li等置换选项
    'INTEGRAL_OPTION', # \su、\pr、\in、\fc\字符、\vc\字符等积分选项
    'ALIGNMENT_OPTION', # \al、\ac、\ar等对齐选项（共享）
    'BOX_OPTION',      # \to、\bo、\le、\ri等边框选项
    'ARRAY_OPTION',    # \con、\vsn、\hsn等数组特有选项
    'LPAREN',          # (
    'RPAREN',          # )
    'COMMA',           # ,
    'SEMICOLON',       # ;
    'IDENTIFIER',      # 标识符
    'NUMBER',          # 数字
    'TEXT',            # 其他文本字符（包括中文）
    'OPERATOR',        # 操作符（+, -, 等）
)

# 标记规则
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','
t_SEMICOLON = r';'

# 忽略空白字符
t_ignore = ' \t'

def t_EQ(t):
    r'EQ'
    return t

# 命令 token 规则 - 必须在普通标识符之前定义
def t_ALIGNMENT_OPTION(t):
    r'\\al|\\ac|\\ar'
    # 匹配 \al、\ac、\ar（数组和重叠共享的对齐选项）
    return t

def t_ARRAY_OPTION(t):
    r'\\co\d+|\\vs\d+|\\hs\d+'
    # 匹配 \con、\vsn、\hsn（数组特有选项）
    return t

def t_BOX_OPTION(t):
    r'\\to|\\bo|\\le|\\ri'
    # 匹配 \to、\bo、\le、\ri
    return t

def t_INTEGRAL_OPTION(t):
    r'\\su|\\pr|\\in|\\fc\\.|\\vc\\.'
    # 匹配 \su、\pr、\in、\fc\字符、\vc\字符
    return t

def t_DISPLACE_OPTION(t):
    r'\\fo\d+|\\ba\d+|\\li'
    # 匹配 \fo数字、\ba数字、\li
    return t

def t_BRACKET_OPTION(t):
    r'\\[lr]c\\.|\\bc\\.'
    # 匹配 \lc\字符、\rc\字符、\bc\字符
    return t

def t_CMD_ARRAY(t):
    r'\\a'
    return t

def t_CMD_BOX(t):
    r'\\x'
    return t

def t_CMD_OVERSTRIKE(t):
    r'\\o'
    return t

def t_CMD_INTEGRAL(t):
    r'\\i'
    return t

def t_CMD_LIST(t):
    r'\\l'
    return t

def t_CMD_DISPLACE(t):
    r'\\d'
    return t

def t_CMD_BRACKET(t):
    r'\\b'
    return t

def t_CMD_FRACTION(t):
    r'\\f'
    return t

def t_CMD_RADICAL(t):
    r'\\r'
    return t

def t_CMD_SUP(t):
    r'\\s\\up\d*'
    return t

def t_CMD_SUB(t):
    r'\\s\\do\d*'
    return t

def t_CMD_ALIGN_INC(t):
    r'\\s\\ai\d*'
    return t

def t_CMD_ALIGN_DEC(t):
    r'\\s\\di\d*'
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # 检查是否是保留字
    if t.value == 'EQ':
        t.type = 'EQ'
    return t

def t_OPERATOR(t):
    r'[+\-*/=<>]'
    return t

def t_TEXT(t):
    r'[^\{\}\\(),;+\-*/=<>\s\d]+'
    # 匹配除了特殊符号、空白、数字之外的所有字符（包括中文）
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"非法字符 '{t.value[0]}'")
    t.lexer.skip(1)

# 构建词法分析器
lexer = lex.lex()
