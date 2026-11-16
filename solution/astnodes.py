"""正则 AST 节点定义与通用工具（可空判定、遍历、反序列化为模式串）。

所有节点带 span=(start, end)，指向原模式串中的区间，用于可解释报告。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional, Tuple

Span = Tuple[int, int]

_META = set("\\.^$*+?{}[]|()-")


def _escape_literal(ch: str) -> str:
    o = ord(ch)
    if ch in _META:
        return "\\" + ch
    if o < 0x20 or o == 0x7F:
        return "\\x%02X" % o
    return ch


def _escape_class_char(ch: str) -> str:
    o = ord(ch)
    if ch in "\\]^-":
        return "\\" + ch
    if o < 0x20 or o == 0x7F:
        return "\\x%02X" % o
    return ch


class Node:
    span: Span


@dataclass
class Empty(Node):
    """空分支 / 空组，匹配空串。"""
    span: Span

    def to_pattern(self, parent: str = "") -> str:
        return ""


@dataclass
class Literal(Node):
    ch: str
    span: Span

    def to_pattern(self, parent: str = "") -> str:
        return _escape_literal(self.ch)


@dataclass
class CharClass(Node):
    """字符类：ranges 为有序码点闭区间列表（按码点处理 Unicode），negated 为取反。"""
    ranges: Tuple[Tuple[int, int], ...]
    negated: bool
    span: Span

    def matches(self, ch: str) -> bool:
        o = ord(ch)
        inside = any(lo <= o <= hi for lo, hi in self.ranges)
        return inside != self.negated

    def to_pattern(self, parent: str = "") -> str:
        parts = []
        for lo, hi in self.ranges:
            if lo == hi:
                parts.append(_escape_class_char(chr(lo)))
            else:
                parts.append(_escape_class_char(chr(lo)) + "-" + _escape_class_char(chr(hi)))
        return "[" + ("^" if self.negated else "") + "".join(parts) + "]"


@dataclass
class Concat(Node):
    items: list
    span: Span

    def to_pattern(self, parent: str = "") -> str:
        body = "".join(c.to_pattern("concat") for c in self.items)
        if parent == "repeat":
            return "(?:" + body + ")"
        return body


@dataclass
class Alt(Node):
    branches: list
    span: Span

    def to_pattern(self, parent: str = "") -> str:
        body = "|".join(b.to_pattern("alt") for b in self.branches)
        if parent in ("concat", "repeat"):
            return "(?:" + body + ")"
        return body


@dataclass
class Group(Node):
    child: Node
    capturing: bool
    span: Span
    index: Optional[int] = None

    def to_pattern(self, parent: str = "") -> str:
        open_ = "(" if self.capturing else "(?:"
        return open_ + self.child.to_pattern("group") + ")"


@dataclass
class Repeat(Node):
    """量词节点。kind ∈ {star, plus, opt} 对应 * + ?。"""
    child: Node
    kind: str
    span: Span

    def to_pattern(self, parent: str = "") -> str:
        sym = {"star": "*", "plus": "+", "opt": "?"}[self.kind]
        return self.child.to_pattern("repeat") + sym


def children(node: Node) -> list:
    if isinstance(node, Concat):
        return list(node.items)
    if isinstance(node, Alt):
        return list(node.branches)
    if isinstance(node, Group):
        return [node.child]
    if isinstance(node, Repeat):
        return [node.child]
    return []


def walk(node: Node, path: str = "$") -> Iterator[tuple]:
    """先序遍历，产出 (node, 路径)。路径形如 $/alt[0]/repeat[0]。"""
    yield node, path
    tag = {
        "Concat": "concat", "Alt": "alt", "Group": "group", "Repeat": "repeat",
    }.get(type(node).__name__)
    for i, c in enumerate(children(node)):
        yield from walk(c, f"{path}/{tag}[{i}]")


def nullable(node: Node) -> bool:
    """节点是否可匹配空串。"""
    if isinstance(node, Empty):
        return True
    if isinstance(node, (Literal, CharClass)):
        return False
    if isinstance(node, Concat):
        return all(nullable(c) for c in node.items)
    if isinstance(node, Alt):
        return any(nullable(b) for b in node.branches)
    if isinstance(node, Group):
        return nullable(node.child)
    if isinstance(node, Repeat):
        if node.kind in ("star", "opt"):
            return True
        return nullable(node.child)  # plus
    raise TypeError(node)


def contains_repeat(node: Node) -> bool:
    """子树（含自身）是否含量词节点。"""
    return any(isinstance(n, Repeat) for n, _ in walk(node))


def could_match(node: Node, ch: str) -> bool:
    """字符 ch 是否可能被该模式消费（用于挑选“必然失配”后缀字符）。"""
    for n, _ in walk(node):
        if isinstance(n, Literal) and n.ch == ch:
            return True
        if isinstance(n, CharClass) and n.matches(ch):
            return True
    return False
