from src.mseq2latex.lexer import lexer
from src.mseq2latex.parser import parser

class MSEQToLatexConverter:
    """Microsoft EQ到LaTeX转换器"""

    def __init__(self):
        self.lexer = lexer
        self.parser = parser

    def convert(self, eq_text):
        """将EQ域文本转换为LaTeX"""
        try:
            # 词法分析
            self.lexer.input(eq_text)

            # 语法分析
            result = self.parser.parse(eq_text, lexer=self.lexer)

            if result:
                res = result.to_latex()
                if result.is_block:
                    return f"\\[ {res} \\]"
                else:
                    return f"$ {res} $"
            else:
                return None

        except Exception as e:
            print(f"转换错误: {e}")
            return None