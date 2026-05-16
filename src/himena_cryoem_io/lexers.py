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
            # Data items (e.g., _rlnVoltage)
            (r"^_\w+", token.Name.Variable),
            # Numbers
            (
                r"[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?(?=\s|\t|$)",
                token.Number.Float,
            ),
            (r"\b\d+(?=\s|\t|$)", token.Number.Integer),
            # Strings (quoted)
            (r"'(\\\\|\\'|[^'])*'", token.String.Single),
            (r'"(\\\\|\\"|[^"])*"', token.String.Double),
            # Values / Identifiers
            (r"\S+", token.Text),
            # Whitespace
            (r"\s+", token.Text.Whitespace),
        ],
    }


class MdocLexer(RegexLexer):
    name = "MDOC"
    aliases = ["mdoc"]
    filenames = ["*.mdoc"]

    tokens = {
        "root": [
            # Titles with brackets
            (r"\[.*?\]", token.Name.Tag),
            # Field assignments (field_name = )
            (r"^\w+\s*=\s*", token.Name.Variable),
            # Numbers
            (
                r"[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?(?=\s|\t|$)",
                token.Number.Float,
            ),
            (r"\b\d+(?=\s|\t|$)", token.Number.Integer),
            # Values / Identifiers
            (r"\S+", token.Text),
            # Whitespace
            (r"\s+", token.Text.Whitespace),
        ],
    }
