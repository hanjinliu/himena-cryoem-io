from pygments.lexer import RegexLexer, words
from pygments import token


class StarLexer(RegexLexer):
    name = "STAR"
    aliases = ["star"]
    filenames = ["*.star"]

    tokens = {
        "root": [
            # Comments
            (r"#.*?\n", token.Comment.Single),
            # Keywords
            (
                words(("loop_",), prefix=r"^", suffix=r"\b"),
                token.Keyword.Reserved,
            ),
            (r"^data_\w*", token.Keyword.Reserved),
            # Numbers
            (r"[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?", token.Number.Float),
            (r"\b\d+\b", token.Number.Integer),
            # Data items (e.g., _rlnVoltage)
            (r"^_\w+", token.Name.Variable),
            # Strings (quoted)
            (r"'(\\\\|\\'|[^'])*'", token.String.Single),
            (r'"(\\\\|\\"|[^"])*"', token.String.Double),
            # Values / Identifiers
            (r"\S+", token.Text),
            # Whitespace
            (r"\s+", token.Text.Whitespace),
        ],
        # copied from the pygments built-in Python lexer
        "numbers": [
            (r"[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?", token.Number.Float),
            (r"\b\d+\b", token.Number.Integer),
        ],
    }
