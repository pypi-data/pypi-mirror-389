import ply.yacc as yacc
from .lexer import tokens
from .ast_nodes import EQField, Fraction, Radical, Superscript, Subscript, SpaceCommand, ExpressionSequence, Bracket, Displace, Integral, List, Overstrike, Box, Array

# 语法规则
def p_eq_field(p):
    '''eq_field : LBRACE EQ expression RBRACE'''
    p[0] = EQField(p[3])

def p_expression_sequence(p):
    '''expression : expression expression'''
    # 处理表达式序列，如 "3 \s\up(y)"
    if isinstance(p[1], ExpressionSequence):
        p[1].add_element(p[2])
        p[0] = p[1]
    else:
        p[0] = ExpressionSequence([p[1], p[2]])

def p_expression_fraction(p):
    '''expression : CMD_FRACTION LPAREN expression COMMA expression RPAREN
                  | CMD_FRACTION LPAREN expression SEMICOLON expression RPAREN'''
    p[0] = Fraction(p[3], p[5])

def p_expression_identifier(p):
    '''expression : IDENTIFIER'''
    p[0] = p[1]

def p_expression_number(p):
    '''expression : NUMBER'''
    p[0] = p[1]

def p_expression_radical(p):
    '''expression : CMD_RADICAL LPAREN expression COMMA expression RPAREN
                  | CMD_RADICAL LPAREN expression RPAREN'''
    if len(p) == 7:  # 有两个参数的根式 \r(degree,radicand)
        p[0] = Radical(p[3], p[5])
    else:  # 只有一个参数的根式 \r(radicand) - 默认为平方根
        p[0] = Radical(None, p[3])

def p_expression_superscript(p):
    '''expression : CMD_SUP LPAREN expression RPAREN'''
    p[0] = Superscript(p[3])

def p_expression_subscript(p):
    '''expression : CMD_SUB LPAREN expression RPAREN'''
    p[0] = Subscript(p[3])

def p_expression_space_ai(p):
    '''expression : CMD_ALIGN_INC LPAREN expression RPAREN'''
    p[0] = SpaceCommand('ai', p[3])

def p_expression_space_di(p):
    '''expression : CMD_ALIGN_DEC LPAREN expression RPAREN'''
    p[0] = SpaceCommand('di', p[3])

def p_expression_bracket_simple(p):
    '''expression : CMD_BRACKET LPAREN expression RPAREN'''
    # 简单括号 \b(expression)
    p[0] = Bracket(p[3])

def p_expression_bracket_with_options(p):
    '''expression : CMD_BRACKET bracket_options LPAREN expression RPAREN'''
    # 带选项的括号 \b \lc\{ \rc\) (expression)
    bracket = Bracket(p[4])
    bracket.set_bracket_options(p[2])
    p[0] = bracket

def p_bracket_options(p):
    '''bracket_options : BRACKET_OPTION
                      | bracket_options BRACKET_OPTION'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]

def p_expression_displace_simple(p):
    '''expression : CMD_DISPLACE LPAREN RPAREN'''
    # 简单置换 \d()
    p[0] = Displace("")

def p_expression_displace_with_content(p):
    '''expression : CMD_DISPLACE LPAREN expression RPAREN'''
    # 带内容的置换 \d(content)
    p[0] = Displace(p[3])

def p_expression_displace_with_options(p):
    '''expression : CMD_DISPLACE displace_options LPAREN RPAREN
                  | CMD_DISPLACE displace_options LPAREN expression RPAREN'''
    # 带选项的置换 \d \fo10 \li() 或 \d \fo10 \li(content)
    if len(p) == 5:
        # 空内容
        displace = Displace("")
    else:
        # 有内容
        displace = Displace(p[4])
    displace.set_displace_options(p[2])
    p[0] = displace

def p_displace_options(p):
    '''displace_options : DISPLACE_OPTION
                       | displace_options DISPLACE_OPTION'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]

def p_expression_integral_simple(p):
    '''expression : CMD_INTEGRAL LPAREN expression COMMA expression COMMA expression RPAREN'''
    # 简单积分 \i(lower,upper,integrand)
    p[0] = Integral(p[3], p[5], p[7])

def p_expression_integral_with_options(p):
    '''expression : CMD_INTEGRAL integral_options LPAREN expression COMMA expression COMMA expression RPAREN'''
    # 带选项的积分 \i \su(1,5,3)
    integral = Integral(p[4], p[6], p[8])
    integral.set_integral_options(p[2])
    p[0] = integral

def p_integral_options(p):
    '''integral_options : INTEGRAL_OPTION
                       | integral_options INTEGRAL_OPTION'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]

def p_expression_list(p):
    '''expression : CMD_LIST LPAREN list_elements RPAREN'''
    # 列表 \l(A,B,C,D,E)
    p[0] = List(p[3])

def p_list_elements(p):
    '''list_elements : expression
                    | list_elements COMMA expression
                    | list_elements SEMICOLON expression'''
    if len(p) == 2:
        # 第一个元素
        p[0] = [p[1]]
    else:
        # 添加新元素到列表
        p[1].append(p[3])
        p[0] = p[1]

def p_expression_overstrike_simple(p):
    '''expression : CMD_OVERSTRIKE LPAREN overstrike_elements RPAREN'''
    # 简单重叠 \o(A,B,C)
    p[0] = Overstrike(p[3])

def p_expression_overstrike_with_options(p):
    '''expression : CMD_OVERSTRIKE overstrike_options LPAREN overstrike_elements RPAREN'''
    # 带选项的重叠 \o \al(A,B,C)
    overstrike = Overstrike(p[4])
    overstrike.set_overstrike_options(p[2])
    p[0] = overstrike

def p_overstrike_options(p):
    '''overstrike_options : ALIGNMENT_OPTION
                         | overstrike_options ALIGNMENT_OPTION'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]

def p_overstrike_elements(p):
    '''overstrike_elements : expression
                          | overstrike_elements COMMA expression'''
    if len(p) == 2:
        # 第一个元素
        p[0] = [p[1]]
    else:
        # 添加新元素到重叠列表
        p[1].append(p[3])
        p[0] = p[1]

def p_expression_array_simple(p):
    '''expression : CMD_ARRAY LPAREN array_elements RPAREN'''
    # 简单数组 \a(A,B,C,D)
    p[0] = Array(p[3])

def p_expression_array_with_options(p):
    '''expression : CMD_ARRAY array_options LPAREN array_elements RPAREN'''
    # 带选项的数组 \a \al \co2 \vs3 \hs3(Axy,Bxy,A,B)
    array = Array(p[4])
    array.set_array_options(p[2])
    p[0] = array

def p_array_options(p):
    '''array_options : ALIGNMENT_OPTION
                    | ARRAY_OPTION
                    | array_options ALIGNMENT_OPTION
                    | array_options ARRAY_OPTION'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]

def p_array_elements(p):
    '''array_elements : expression
                     | array_elements COMMA expression'''
    if len(p) == 2:
        # 第一个元素
        p[0] = [p[1]]
    else:
        # 添加新元素到数组
        p[1].append(p[3])
        p[0] = p[1]

def p_expression_box_simple(p):
    '''expression : CMD_BOX LPAREN expression RPAREN'''
    # 简单边框 \x(element)
    p[0] = Box(p[3])

def p_expression_box_with_options(p):
    '''expression : CMD_BOX box_options LPAREN expression RPAREN'''
    # 带选项的边框 \x \to \bo(element)
    box = Box(p[4])
    box.set_box_options(p[2])
    p[0] = box

def p_box_options(p):
    '''box_options : BOX_OPTION
                  | box_options BOX_OPTION'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]

def p_expression_text(p):
    '''expression : TEXT'''
    p[0] = p[1]

def p_expression_operator(p):
    '''expression : OPERATOR'''
    p[0] = p[1]

def p_error(p):
    if p:
        print(f"语法错误在标记 {p.type}")
    else:
        print("语法错误在文件末尾")

# 构建语法分析器
parser = yacc.yacc()
