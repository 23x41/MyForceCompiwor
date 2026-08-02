#!/usr/bin/env python3
"""
Stage 1 Compiler: int main() { return <number>; }
Generates x86-64 AT&T assembly for Linux.

Usage:
    python3 compiler.py test.c
    gcc test.s -o test
    ./test ; echo $?
"""

import sys
from dataclasses import dataclass
from typing import List


# ---------- Tokens ----------
@dataclass
class Token:
    type: str
    value: str
    line: int = 1


# ---------- AST Nodes ----------
@dataclass
class Program:
    function: "Function"


@dataclass
class Function:
    name: str
    body: "Return"


@dataclass
class Return:
    expr: "Constant"


@dataclass
class Constant:
    value: int


# ---------- Lexer ----------
def tokenize(source: str) -> List[Token]:
    tokens = []
    i = 0
    line = 1
    keywords = {"int", "main", "return"}

    while i < len(source):
        c = source[i]

        if c in " \t\r":
            i += 1
            continue
        if c == "\n":
            line += 1
            i += 1
            continue

        if c in "(){};":
            tokens.append(Token(c, c, line))
            i += 1
            continue

        if c.isdigit():
            start = i
            while i < len(source) and source[i].isdigit():
                i += 1
            tokens.append(Token("NUMBER", source[start:i], line))
            continue

        if c.isalpha() or c == "_":
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                i += 1
            word = source[start:i]
            tok_type = word if word in keywords else "IDENT"
            tokens.append(Token(tok_type, word, line))
            continue

        raise SyntaxError(f"Unexpected character '{c}' on line {line}")

    tokens.append(Token("EOF", "", line))
    return tokens


# ---------- Parser (Recursive Descent) ----------
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def eat(self, expected_type: str) -> Token:
        tok = self.current()
        if tok.type != expected_type:
            raise SyntaxError(
                f"Expected {expected_type}, got {tok.type} "
                f"('{tok.value}') on line {tok.line}"
            )
        self.pos += 1
        return tok

    def parse(self) -> Program:
        # int main ( ) { return <expr> ; }
        self.eat("int")
        self.eat("main")
        self.eat("(")
        self.eat(")")
        self.eat("{")
        self.eat("return")
        expr = self.parse_expr()
        self.eat(";")
        self.eat("}")
        self.eat("EOF")
        return Program(Function("main", Return(expr)))

    def parse_expr(self) -> Constant:
        tok = self.eat("NUMBER")
        return Constant(int(tok.value))


# ---------- Code Generator (x86-64 AT&T) ----------
def generate(program: Program) -> str:
    """Emit a complete assembly file."""
    value = program.function.body.expr.value
    lines = [
        "    .globl main",
        "main:",
        f"    movq ${value}, %rax",
        "    ret",
        ""
    ]
    return "\n".join(lines)


# ---------- Driver ----------
def compile_file(source_path: str, output_path: str = None):
    with open(source_path) as f:
        source = f.read()

    tokens = tokenize(source)
    program = Parser(tokens).parse()
    asm = generate(program)

    if output_path is None:
        output_path = source_path.rsplit(".", 1)[0] + ".s"

    with open(output_path, "w") as f:
        f.write(asm)

    print(f"Generated: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <file.c> [output.s]")
        sys.exit(1)

    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    compile_file(src, out)
