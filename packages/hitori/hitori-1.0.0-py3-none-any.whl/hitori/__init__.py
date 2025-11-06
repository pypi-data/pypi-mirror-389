from __future__ import annotations


class ParseException(Exception):
    pass


class SerializationException(Exception):
    pass


type SExpression = list[SExpression] | str


class Parser:
    """An S-Expression parser"""

    def __init__(self):
        self._cur_atom = ""
        self._stack = [[]]
        self._inside_comment = False
        self._need_whitespace = False
        self._inside_unquoted = False
        self._inside_quoted = False
        self._escape_active = False

    def _push_char(self, c: str):
        self._cur_atom += c

    def _push_atom(self):
        self._stack[-1].append(self._cur_atom)
        self._cur_atom = ""

    def _start_list(self):
        self._stack.append([])

    def _end_list(self):
        self._stack[-2].append(self._stack[-1])
        self._stack.pop()

    def parse(self, s: str):
        """
        Parses the given string into an S-Expression.

        This method can be called multiple times which might be useful if
        the expression is received over the network and therefore split across
        multiple strings. For example: calling `parse` with "a", "b" and then
        "c" is the same as calling it once with "abc".
        To retrieve the parsed value, call `Parser.finish`.
        """

        for val in s:
            c = ord(val)
            if (c < 0x20 and c != 0x9 and c != 0xa and c != 0xd) or c == 0x7f:
                raise ParseException("invalid character")
            if self._inside_comment:
                if val == "\n":
                    self._inside_comment = False
            elif self._escape_active:
                self._push_char(val)
                self._escape_active = False
            elif val == "\\":
                if self._need_whitespace:
                    raise ParseException("atom must be followed by a whitespace character or comment before the next atom starts")
                self._escape_active = True
                if not self._inside_quoted:
                    self._inside_unquoted = True
            elif val == ";" and not self._inside_quoted:
                if self._inside_unquoted:
                    self._inside_unquoted = False
                    self._push_atom()
                self._inside_comment = True
                self._need_whitespace = False
            elif val == '"':
                if self._inside_unquoted:
                    raise ParseException("a double quote is not allowed inside of an unquoted atom")
                if self._need_whitespace:
                    raise ParseException("atom must be followed by a whitespace character or comment before the next atom starts")

                if self._inside_quoted:
                    self._inside_quoted = False
                    self._push_atom()
                    self._need_whitespace = True
                else:
                    self._inside_quoted = True
            elif val == "(" and not self._inside_quoted:
                if self._cur_atom != "":
                    self._push_atom()
                    self._inside_unquoted = False
                self._need_whitespace = False
                self._start_list()
            elif val == ")" and not self._inside_quoted:
                if self._cur_atom != "":
                    self._push_atom()
                    self._inside_unquoted = False
                self._need_whitespace = False
                self._end_list()
            elif not self._inside_quoted and (val == " " or c == 0xa or c == 0x9 or c == 0xd):
                if self._cur_atom != "":
                    self._push_atom()
                    self._inside_unquoted = False
                self._need_whitespace = False
            else:
                if self._need_whitespace:
                    raise ParseException("atom must be followed by a whitespace character or comment before the next atom starts")
                if not self._inside_quoted:
                    self._inside_unquoted = True
                self._push_char(val)

    def finish(self) -> list[SExpression]:
        """Signals that no more data will be passed and returns the parsed S-Expression."""
        if len(self._stack) > 1:
            raise ParseException("at least one list is not closed")
        if len(self._stack) == 0:
            raise ParseException("too many closing parenthesis")
        if self._escape_active:
            raise ParseException("incomplete escape sequence")
        elif self._cur_atom != "" and self._inside_unquoted:
            self._push_atom()
        elif self._inside_quoted:
            raise ParseException("missing trailing quote for atom")
        return self._stack[0]


def parse(data: str) -> list[SExpression]:
    """Parses a string into an S-Expression"""
    parser = Parser()
    parser.parse(data)
    return parser.finish()


def serialize(expressions: list[SExpression], compact: bool = False) -> str:
    """
    Serializes a list of S-Expressions to a string

    The argument `compact` controls if spaces between elements in a list should
    be left out when they are not necessary.
    """

    s = ""
    was_atom = False
    for i, sexp in enumerate(expressions):
        is_atom = isinstance(sexp, str)
        if compact and was_atom and is_atom:
            s += " "
        if is_atom:
            quote = sexp == "" or any(c == " " or c == "(" or c == ")" or c == ";" or c == "\n" or c == "\r" or c == "\t" for c in sexp)
            if quote:
                s += '"'
            for c in sexp:
                if c == '"' or c == "\\":
                    s += "\\"
                s += c
            if quote:
                s += '"'
        elif isinstance(sexp, list):
            s += "("
            s += serialize(sexp, compact)
            s += ")"
        else:
            raise SerializationException(f"the value {sexp} of type {type(sexp)} cannot be serialized into an s-expression")
        if not compact and i < len(expressions) - 1:
            s += " "
        was_atom = is_atom
    return s

