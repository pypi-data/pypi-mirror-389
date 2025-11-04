"""Console (impressão) de árvores em texto.

Fornece a classe PrintTree para imprimir árvores verticalmente no terminal.
"""

from itertools import zip_longest
import re


# --- Utilitários mínimos cientes de ANSI ---
_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_RESET = "\x1b[0m"


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _text_width(text: str) -> int:
    # Largura simplificada (ignora sequências ANSI)
    return len(_strip_ansi(text))


def _ljust(text: str, amount: int, padding: str = ' ') -> str:
    pad = max(0, amount - _text_width(text))
    return text + (padding * pad)


class _NodeFormatter:
    """Formata um nó como bloco de texto com largura conhecida."""

    @classmethod
    def from_string(cls, content: str):
        lines = content.split('\n')
        width = max(_text_width(line) for line in lines)
        return cls(lines, width=width)

    def __init__(self, lines, *, width: int, middle_width: int = None):
        self.lines = lines
        self.width = width
        self.middle_width = middle_width

    def color_bg(self, color: str, add_space: bool) -> None:
        if add_space:
            self.lines = [f'{ color } { _ljust(line, self.width) } { _RESET }' for line in self.lines]
            self.width += 2
        else:
            self.lines = [f'{ color }{ _ljust(line, self.width) }{ _RESET }' for line in self.lines]

    def to_str(self) -> str:
        return '\n'.join(self.lines)

    def get_middle_width(self) -> int:
        if self.middle_width is None:
            return sum(divmod(self.width, 2)) - 1
        return self.middle_width


def _join_boxes(boxes):
    lines = [
        ' '.join(_ljust(line, boxes[i].width) for i, line in enumerate(lines))
        for lines in zip_longest(*(box.lines for box in boxes), fillvalue='')
    ]
    width = sum(box.width for box in boxes) + len(boxes) - 1
    return lines, width


def _add_pipes(boxes, lines) -> int:
    padding = ' ' * boxes[0].get_middle_width()
    pipes = '┌'
    for prev, box in zip(boxes, boxes[1:]):
        pipes += '─' * (prev.width - prev.get_middle_width() + box.get_middle_width()) + '┬'
    middle_of_pipes = sum(divmod(len(pipes), 2)) - 1
    pipes = (
        padding + pipes[:middle_of_pipes]
        + {"─": "┴", "┬": "┼", "┌": "├", "┐": "┤"}[pipes[middle_of_pipes]]
        + pipes[middle_of_pipes + 1:-1] + '┐'
    )
    lines.insert(0, pipes)
    return len(padding) + middle_of_pipes


def _join_horizontally(boxes):
    lines, width = _join_boxes(boxes)
    middle = _add_pipes(boxes, lines)
    return _NodeFormatter(lines, width=width, middle_width=middle)


def _add_parent(parent, children):
    parent_middle, children_middle = parent.get_middle_width(), children.get_middle_width()
    parent_width, children_width = parent.width, children.width
    if parent_middle == children_middle:
        lines = parent.lines + children.lines
        middle = parent_middle
    elif parent_middle < children_middle:
        padding = ' ' * (children_middle - parent_middle)
        lines = [padding + line for line in parent.lines] + children.lines
        parent_width += children_middle - parent_middle
        middle = children_middle
    else:
        padding = ' ' * (parent_middle - children_middle)
        lines = parent.lines + [padding + line for line in children.lines]
        children_width += parent_middle - children_middle
        middle = parent_middle
    return _NodeFormatter(lines, width=max(parent_width, children_width), middle_width=middle)


class _TreeFormatter:
    """Formata a árvore em linhas (apenas vertical)."""

    def __init__(self, get_children, get_val, color):
        self.get_children = get_children
        self.get_node_val = get_val
        self.color = color

    def format(self, node):
        return self._tree_vertical(node).to_str().rstrip()

    def _tree_vertical(self, node):
        children = self.get_children(node)
        cur = self._format_node(node)
        if children:
            children_fmt = [self._tree_vertical(child) for child in children]
            if len(children_fmt) == 1:
                only = children_fmt[0]
                only.lines.insert(0, ' ' * only.get_middle_width() + '|')
                children_node = only
            else:
                children_node = _join_horizontally(children_fmt)
            cur = _add_parent(cur, children_node)
        return cur

    def _format_node(self, node):
        contents = str(self.get_node_val(node))
        nf = _NodeFormatter.from_string(contents)
        if self.color:
            nf.color_bg(self.color, add_space=True)
        return nf


class PrintTree:
    """Imprime a árvore no console em formato vertical."""

    def __init__(self, get_children=None, get_val=None, *, color: str = ""):
        self.default_get_children = get_children or (lambda x: x.children)
        self.default_get_node_val = get_val or (lambda x: x.value)
        self.default_color = color

    def __call__(self, node, *, color: str = None):
        fmt = _TreeFormatter(
            get_children=self.default_get_children,
            get_val=self.default_get_node_val,
            color=self.default_color if color is None else color,
        )
        print(fmt.format(node))

