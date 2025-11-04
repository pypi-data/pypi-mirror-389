class ASTNode:
    """AST节点基类"""

    def __init__(self, is_block=False):
        self.is_block = is_block

class EQField(ASTNode):
    """EQ域节点"""
    def __init__(self, expression):
        super().__init__()
        self.expression = expression
        if isinstance(expression, ASTNode):
            self.is_block = expression.is_block or self.is_block

    def to_latex(self):
        return self.expression.to_latex()

class Fraction(ASTNode):
    """分式节点"""
    def __init__(self, numerator, denominator):
        super().__init__()
        self.numerator = numerator
        self.denominator = denominator
        if isinstance(numerator, ASTNode):
            self.is_block = numerator.is_block or self.is_block
        if isinstance(denominator, ASTNode):
            self.is_block = denominator.is_block or self.is_block

    def to_latex(self):
        num = self._format_expression(self.numerator)
        den = self._format_expression(self.denominator)
        return f"\\frac{{{num}}}{{{den}}}"

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class Radical(ASTNode):
    """根式节点"""
    def __init__(self, degree, radicand):
        super().__init__()
        self.degree = degree  # 根次数，None表示平方根
        self.radicand = radicand  # 被开方数
        if isinstance(radicand, ASTNode):
            self.is_block = radicand.is_block or self.is_block
        if degree and isinstance(degree, ASTNode):
            self.is_block = degree.is_block or self.is_block

    def to_latex(self):
        radicand = self._format_expression(self.radicand)

        if self.degree is None:
            # 平方根
            return f"\\sqrt{{{radicand}}}"
        else:
            # n次根
            degree = self._format_expression(self.degree)
            return f"\\sqrt[{degree}]{{{radicand}}}"

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class Superscript(ASTNode):
    """上标节点"""
    def __init__(self, content):
        super().__init__()
        self.content = content
        if isinstance(content, ASTNode):
            self.is_block = content.is_block or self.is_block

    def to_latex(self):
        content = self._format_expression(self.content)
        return f"^{{{content}}}"

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class Subscript(ASTNode):
    """下标节点"""
    def __init__(self, content):
        super().__init__()
        self.content = content
        if isinstance(content, ASTNode):
            self.is_block = content.is_block or self.is_block

    def to_latex(self):
        content = self._format_expression(self.content)
        return f"_{{{content}}}"

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class SpaceCommand(ASTNode):
    """空间命令节点（ai, di）"""
    def __init__(self, command_type, content):
        super().__init__()
        self.command_type = command_type  # 'ai' 或 'di'
        self.content = content
        if isinstance(content, ASTNode):
            self.is_block = content.is_block or self.is_block

    def to_latex(self):
        # 原样输出括号里的内容
        content = self._format_expression(self.content)
        return content

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class CombinedScript(ASTNode):
    """组合脚本节点（处理相邻的上下标）"""
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

        for element in self.elements:
            if isinstance(element, ASTNode):
                self.is_block = element.is_block or self.is_block

    def to_latex(self):
        result = ""
        for element in self.elements:
            if isinstance(element, ASTNode):
                result += element.to_latex()
            else:
                result += str(element)
        return result

class ExpressionSequence(ASTNode):
    """表达式序列节点"""
    def __init__(self, elements):
        super().__init__()
        self.elements = elements if isinstance(elements, list) else [elements]

        for element in self.elements:
            if isinstance(element, ASTNode):
                self.is_block = element.is_block or self.is_block

    def add_element(self, element):
        """添加新元素到序列"""
        self.elements.append(element)

    def to_latex(self):
        result = ""
        for i, element in enumerate(self.elements):
            # 对于中文字符或特殊文本，在LaTeX中需要特殊处理
            if isinstance(element, str) and any('\u4e00' <= char <= '\u9fff' for char in element):
                # 中文字符用 \text{} 包围
                result += f"\\text{{{element}}}"
            elif isinstance(element, ASTNode):
                result += element.to_latex()
            else:
                result += str(element)

            # 在某些情况下添加空格
            if i < len(self.elements) - 1:
                next_element = self.elements[i + 1]
                if not (isinstance(next_element, (Superscript, Subscript))):
                    result += " "

        return result

class Bracket(ASTNode):
    """括号节点"""
    def __init__(self, content, left_bracket='(', right_bracket=')'):
        super().__init__()
        self.content = content
        self.left_bracket = left_bracket
        self.right_bracket = right_bracket
        if isinstance(content, ASTNode):
            self.is_block = content.is_block or self.is_block

    def set_bracket_options(self, options):
        """根据括号选项设置左右括号"""
        # 从左到右处理选项，后面的会覆盖前面的
        for option in options:
            option_type, char = self._parse_bracket_option(option)
            if option_type == 'lc':
                self.left_bracket = char
            elif option_type == 'rc':
                self.right_bracket = char
            elif option_type == 'bc':
                self.left_bracket = char
                self.right_bracket = self._get_corresponding_bracket(char)

    def _get_corresponding_bracket(self, char):
        """获取对应的右括号"""
        bracket_pairs = {
            '(': ')',
            '[': ']',
            '{': '}',
            '<': '>',
        }
        return bracket_pairs.get(char, char)

    def _parse_bracket_option(self, option):
        """解析括号选项"""
        # option格式：\lc\字符、\rc\字符、\bc\字符
        if option.startswith('\\lc\\'):
            return 'lc', option[4]
        elif option.startswith('\\rc\\'):
            return 'rc', option[4]
        elif option.startswith('\\bc\\'):
            return 'bc', option[4]
        return None, None

    def _get_latex_bracket(self, char):
        """将字符转换为LaTeX括号格式"""
        bracket_map = {
            '(': '(',
            ')': ')',
            '[': '[',
            ']': ']',
            '{': '\\{',
            '}': '\\}',
            '<': '\\langle',
            '>': '\\rangle',
            '|': '|',
            '\\': '\\backslash'
        }
        return bracket_map.get(char, char)

    def to_latex(self):
        content = self._format_expression(self.content)
        left = self._get_latex_bracket(self.left_bracket)
        right = self._get_latex_bracket(self.right_bracket)

        # 如果左右括号相同且不是常见的配对括号，使用相同的符号
        if self.left_bracket == self.right_bracket and self.left_bracket not in '()[]{}<>':
            return f"\\left{left} {content} \\right{right}"

        # 处理配对括号
        if self.left_bracket in '{[(<':
            # 自动配对
            pair_map = {'{': '}', '[': ']', '(': ')', '<': '>'}
            if self.right_bracket == pair_map.get(self.left_bracket, ')'):
                return f"\\left{left} {content} \\right{right}"

        return f"\\left{left} {content} \\right{right}"

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class Displace(ASTNode):
    """置换指令节点"""
    def __init__(self, content):
        super().__init__()
        self.content = content
        self.options = {}  # 存储选项值：{fo: n, ba: n, li: True}

        if isinstance(content, ASTNode):
            self.is_block = content.is_block or self.is_block

    def set_displace_options(self, options):
        """根据置换选项设置参数"""
        # 从左到右处理选项，后面的会覆盖前面的
        for option in options:
            option_type, value = self._parse_displace_option(option)
            if option_type:
                self.options[option_type] = value

    def _parse_displace_option(self, option):
        """解析置换选项"""
        # option格式：\fo数字、\ba数字、\li
        if option.startswith('\\fo'):
            # 提取数字
            try:
                value = int(option[3:])
                return 'fo', value
            except ValueError:
                return None, None
        elif option.startswith('\\ba'):
            # 提取数字
            try:
                value = int(option[3:])
                return 'ba', value
            except ValueError:
                return None, None
        elif option == '\\li':
            return 'li', True
        return None, None

    def to_latex(self):
        """将内容转换为\text{}格式，忽略选项效果"""
        content = self._format_expression(self.content)
        return f"\\text{{{content}}}"

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class Integral(ASTNode):
    """积分指令节点"""
    def __init__(self, lower_limit=None, upper_limit=None, integrand=None):
        super().__init__()
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.integrand = integrand
        self.options = {}  # 存储选项值：{su: True, pr: True, in: True, fc: char, vc: char}
        self.symbol_type = 'integral'  # 默认为积分符号
        self.is_block = False  # 是否为内联格式

        if isinstance(lower_limit, ASTNode):
            self.is_block = lower_limit.is_block or self.is_block
        if isinstance(upper_limit, ASTNode):
            self.is_block = upper_limit.is_block or self.is_block
        if isinstance(integrand, ASTNode):
            self.is_block = integrand.is_block or self.is_block

    def set_integral_options(self, options):
        """根据积分选项设置参数"""
        # 从左到右处理选项，后面的会覆盖前面的
        for option in options:
            option_type, value = self._parse_integral_option(option)
            if option_type:
                self.options[option_type] = value
                # 根据选项设置符号类型
                if option_type == 'su':
                    self.symbol_type = 'sum'
                elif option_type == 'pr':
                    self.symbol_type = 'product'
                elif option_type == 'in':
                    pass # 默认为内联格式，若子节点需要块级环境，则会覆盖，故无需处理
                elif option_type in ['fc', 'vc']:
                    self.symbol_type = 'custom'

    def _parse_integral_option(self, option):
        """解析积分选项"""
        # option格式：\su、\pr、\in、\fc\字符、\vc\字符
        if option == '\\su':
            return 'su', True
        elif option == '\\pr':
            return 'pr', True
        elif option == '\\in':
            return 'in', True
        elif option.startswith('\\fc\\'):
            return 'fc', option[4]  # 提取字符
        elif option.startswith('\\vc\\'):
            return 'vc', option[4]  # 提取字符
        return None, None

    def to_latex(self):
        """将积分转换为LaTeX格式"""
        lower = self._format_expression(self.lower_limit) if self.lower_limit is not None else ""
        upper = self._format_expression(self.upper_limit) if self.upper_limit is not None else ""
        integrand = self._format_expression(self.integrand)

        # 根据符号类型选择符号
        if self.symbol_type == 'sum':
            symbol = '\\sum'
        elif self.symbol_type == 'product':
            symbol = '\\prod'
        elif self.symbol_type == 'custom':
            # 对于自定义符号，暂时使用默认积分符号
            symbol = '\\int'
        else:
            symbol = '\\int'

        # 根据是否内联格式决定上下限位置
        if self.is_block and self.symbol_type in ['sum', 'product']:
            # 内联格式：限制显示在右侧
            if upper and lower:
                return f"{symbol}_{{{lower}}}^{{{upper}}} {{{integrand}}}"
            elif lower:
                return f"{symbol}_{{{lower}}} {{{integrand}}}"
            elif upper:
                return f"{symbol}^{{{upper}}} {{{integrand}}}"
            else:
                return f"{symbol} {{{integrand}}}"
        else:
            # 标准格式：限制显示在上下方
            if upper and lower:
                return f"{symbol}_{{{lower}}}^{{{upper}}} {{{integrand}}}"
            elif lower:
                return f"{symbol}_{{{lower}}} {{{integrand}}}"
            elif upper:
                return f"{symbol}^{{{upper}}} {{{integrand}}}"
            else:
                return f"{symbol} {{{integrand}}}"

    def _format_expression(self, expr):
        if expr is None:
            return ""
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class List(ASTNode):
    """列表节点"""
    def __init__(self, elements):
        super().__init__()
        self.elements = elements if isinstance(elements, list) else [elements]

        for element in self.elements:
            if isinstance(element, ASTNode):
                self.is_block = element.is_block or self.is_block

    def add_element(self, element):
        """添加新元素到列表"""
        self.elements.append(element)

    def to_latex(self):
        """将列表转换为LaTeX格式，简单用逗号连接"""
        formatted_elements = []
        for element in self.elements:
            if isinstance(element, ASTNode):
                formatted_elements.append(element.to_latex())
            else:
                formatted_elements.append(str(element))

        return ",".join(formatted_elements)

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class Overstrike(ASTNode):
    """重叠指令节点"""
    def __init__(self, elements):
        super().__init__()
        self.elements = elements if isinstance(elements, list) else [elements]
        self.options = {}  # 存储选项值：{al: True, ac: True, ar: True}
        self.alignment = 'ac'  # 默认为居中对齐

        for element in self.elements:
            if isinstance(element, ASTNode):
                self.is_block = element.is_block or self.is_block

    def add_element(self, element):
        """添加新元素到重叠列表"""
        self.elements.append(element)

    def set_overstrike_options(self, options):
        """根据重叠选项设置参数"""
        # 从左到右处理选项，后面的会覆盖前面的
        for option in options:
            option_type = self._parse_overstrike_option(option)
            if option_type:
                self.options[option_type] = True
                self.alignment = option_type  # 设置对齐方式

    def _parse_overstrike_option(self, option):
        """解析重叠选项"""
        # option格式：\al、\ac、\ar
        if option == '\\al':
            return 'al'  # 左对齐
        elif option == '\\ac':
            return 'ac'  # 居中对齐
        elif option == '\\ar':
            return 'ar'  # 右对齐
        return None

    def to_latex(self):
        """将重叠元素转换为LaTeX格式，简单用逗号连接"""
        formatted_elements = []
        for element in self.elements:
            if isinstance(element, ASTNode):
                formatted_elements.append(element.to_latex())
            else:
                formatted_elements.append(str(element))

        return ",".join(formatted_elements)

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class Array(ASTNode):
    """数组指令节点"""
    def __init__(self, elements):
        super().__init__(is_block=True)  # 强制设置为块级元素
        self.elements = elements if isinstance(elements, list) else [elements]
        self.options = {}  # 存储选项值：{al: True, ac: True, ar: True, co: n, vs: n, hs: n}
        self.alignment = 'ac'  # 默认居中对齐
        self.columns = 1  # 默认1列
        self.vertical_spacing = 0  # 默认垂直间距
        self.horizontal_spacing = 0  # 默认水平间距

        # for element in self.elements:
        #     if isinstance(element, ASTNode):
        #         self.is_block = element.is_block or self.is_block

    def add_element(self, element):
        """添加新元素到数组"""
        self.elements.append(element)

    def set_array_options(self, options):
        """根据数组选项设置参数"""
        # 从左到右处理选项，后面的会覆盖前面的
        for option in options:
            option_type, value = self._parse_array_option(option)
            if option_type:
                self.options[option_type] = value
                # 根据选项设置参数
                if option_type == 'al':
                    self.alignment = 'al'  # 左对齐
                elif option_type == 'ac':
                    self.alignment = 'ac'  # 居中对齐
                elif option_type == 'ar':
                    self.alignment = 'ar'  # 右对齐
                elif option_type == 'co':
                    self.columns = value  # 列数
                elif option_type == 'vs':
                    self.vertical_spacing = value  # 垂直间距（存储但不使用）
                elif option_type == 'hs':
                    self.horizontal_spacing = value  # 水平间距（存储但不使用）

    def _parse_array_option(self, option):
        """解析数组选项"""
        # option格式：\al、\ac、\ar、\con、\vsn、\hsn
        if option == '\\al':
            return 'al', True
        elif option == '\\ac':
            return 'ac', True
        elif option == '\\ar':
            return 'ar', True
        elif option.startswith('\\co'):
            # 提取数字
            try:
                value = int(option[3:])
                return 'co', value
            except ValueError:
                return None, None
        elif option.startswith('\\vs'):
            # 提取数字
            try:
                value = int(option[3:])
                return 'vs', value
            except ValueError:
                return None, None
        elif option.startswith('\\hs'):
            # 提取数字
            try:
                value = int(option[3:])
                return 'hs', value
            except ValueError:
                return None, None
        return None, None

    def to_latex(self):
        """将数组转换为LaTeX的matrix环境格式"""
        if not self.elements:
            return "\\begin{matrix}\\end{matrix}"
        
        # 格式化元素
        formatted_elements = []
        for element in self.elements:
            if isinstance(element, ASTNode):
                formatted_elements.append(element.to_latex())
            else:
                formatted_elements.append(str(element))
        
        # 按列数排列元素
        rows = []
        for i in range(0, len(formatted_elements), self.columns):
            row_elements = formatted_elements[i:i + self.columns]
            # 如果行不满，用空字符串填充
            while len(row_elements) < self.columns:
                row_elements.append("")
            rows.append(" & ".join(row_elements))
        
        # 生成matrix环境
        matrix_content = " \\\\ ".join(rows)
        return f"\\begin{{matrix}}{matrix_content}\\end{{matrix}}"

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)

class Box(ASTNode):
    """边框指令节点"""
    def __init__(self, content):
        super().__init__()
        self.content = content
        self.options = {}  # 存储选项值：{to: True, bo: True, le: True, ri: True}
        self.borders = set()  # 存储边框类型

        if isinstance(content, ASTNode):
            self.is_block = content.is_block or self.is_block

    def set_box_options(self, options):
        """根据边框选项设置参数"""
        # 处理所有选项，可以组合使用
        for option in options:
            option_type = self._parse_box_option(option)
            if option_type:
                self.options[option_type] = True
                self.borders.add(option_type)

    def _parse_box_option(self, option):
        """解析边框选项"""
        # option格式：\to、\bo、\le、\ri
        if option == '\\to':
            return 'to'  # 上边框
        elif option == '\\bo':
            return 'bo'  # 下边框
        elif option == '\\le':
            return 'le'  # 左边框
        elif option == '\\ri':
            return 'ri'  # 右边框
        return None

    def to_latex(self):
        """将边框元素转换为LaTeX格式，只输出括号内的表达式"""
        if isinstance(self.content, ASTNode):
            return self.content.to_latex()
        else:
            return str(self.content)

    def _format_expression(self, expr):
        if isinstance(expr, ASTNode):
            return expr.to_latex()
        else:
            return str(expr)
