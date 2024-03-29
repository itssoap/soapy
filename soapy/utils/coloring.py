from pygments import highlight, util
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from typing import Literal

def colors(text: bytes | Literal['']) -> str:
    lexer = guess_lexer(text)  
    formatter = HtmlFormatter(linenos=True, style='github-dark')
    return highlight(text, lexer, formatter)