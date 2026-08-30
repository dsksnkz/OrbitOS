#!/usr/bin/env python3
"""A small, safe calculator for the OrbitOS utility menu."""

from __future__ import annotations

import ast
import math
import operator
import subprocess


BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
NAMES = {"pi": math.pi, "e": math.e}


def evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in NAMES:
        return NAMES[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
        left, right = evaluate(node.left), evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent is too large")
        return BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
        return UNARY[type(node.op)](evaluate(node.operand))
    raise ValueError("unsupported expression")


def main() -> None:
    prompt = subprocess.run(
        ["rofi", "-dmenu", "-p", "Calculate"], input="", text=True, capture_output=True, check=False
    ).stdout.strip()
    if not prompt:
        return
    try:
        result = evaluate(ast.parse(prompt, mode="eval"))
        output = f"{result:g}"
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError) as exc:
        subprocess.run(["notify-send", "Calculator", str(exc)], check=False)
        return
    subprocess.run(["wl-copy"], input=output, text=True, check=False)
    subprocess.run(["notify-send", "Calculator", f"{prompt} = {output}\nCopied to clipboard"], check=False)


if __name__ == "__main__":
    main()
