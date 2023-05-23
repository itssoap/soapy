from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

def colors(text: str) -> str:
    lexer = get_lexer_by_name(guess_lexer(text).name, stripall=True)
    formatter = HtmlFormatter(linenos=True, cssclass="source")
    return highlight(text, lexer, formatter)