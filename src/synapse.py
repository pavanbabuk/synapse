#!/usr/bin/env python3
"""
Synapse (SYN-IR) Compiler & Runtime Engine.
Features:
1. Lexer & S-Expression Parser
2. Nano-Interpreter (instant low-memory execution)
3. Native C99 Code Generator (compiles to freestanding binary via clang)
4. Human View Projector (decompiles SYN-IR to clean, idiomatic Python)
"""

import sys
import os
import re
import subprocess
import tempfile
from typing import Any, List

# ==========================================
# 1. TOKENIZER & PARSER
# ==========================================

class Token:
    def __init__(self, type_: str, value: str, line: int):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

def tokenize(source: str) -> List[Token]:
    tokens = []
    line_num = 1
    i = 0
    n = len(source)

    while i < n:
        c = source[i]
        if c == '\n':
            line_num += 1
            i += 1
        elif c in ' \t\r':
            i += 1
        elif c == ';' and i + 1 < n and source[i + 1] == ';':
            while i < n and source[i] != '\n':
                i += 1
        elif c == '(':
            tokens.append(Token('LPAREN', '(', line_num))
            i += 1
        elif c == ')':
            tokens.append(Token('RPAREN', ')', line_num))
            i += 1
        elif c == '"':
            start = i + 1
            i += 1
            val = []
            while i < n and source[i] != '"':
                if source[i] == '\\' and i + 1 < n:
                    val.append(source[i:i+2])
                    i += 2
                else:
                    val.append(source[i])
                    i += 1
            if i >= n:
                raise SyntaxError(f"Unterminated string literal on line {line_num}")
            i += 1
            tokens.append(Token('STRING', "".join(val), line_num))
        else:
            start = i
            while i < n and source[i] not in ' \t\r\n();':
                i += 1
            word = source[start:i]
            if re.match(r'^-?\d+\.\d+$', word):
                tokens.append(Token('FLOAT', word, line_num))
            elif re.match(r'^-?\d+$', word):
                tokens.append(Token('INT', word, line_num))
            elif word in ('true', 'false'):
                tokens.append(Token('BOOL', word, line_num))
            else:
                tokens.append(Token('SYMBOL', word, line_num))
    return tokens

def parse_s_expr(tokens: List[Token]) -> List[Any]:
    def parse_one(index: int):
        token = tokens[index]
        if token.type == 'LPAREN':
            elements = []
            index += 1
            while index < len(tokens) and tokens[index].type != 'RPAREN':
                elem, index = parse_one(index)
                elements.append(elem)
            if index >= len(tokens):
                raise SyntaxError("Unmatched '('")
            return elements, index + 1
        elif token.type == 'RPAREN':
            raise SyntaxError(f"Unexpected ')' at line {token.line}")
        else:
            return token, index + 1

    exprs = []
    idx = 0
    while idx < len(tokens):
        expr, idx = parse_one(idx)
        exprs.append(expr)
    return exprs

# ==========================================
# 2. NANO INTERPRETER (Micro-runtime)
# ==========================================

class NanoEnv:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}

    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Undefined symbol: {name}")

    def set(self, name: str, value: Any):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.set(name, value)
            return
        raise NameError(f"Cannot set undefined variable: {name}")

    def define(self, name: str, value: Any):
        self.vars[name] = value

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class NanoInterpreter:
    def __init__(self):
        self.functions = {}
        self.global_env = NanoEnv()

    def eval(self, node: Any, env: NanoEnv) -> Any:
        if isinstance(node, Token):
            if node.type == 'INT':
                return int(node.value)
            elif node.type == 'FLOAT':
                return float(node.value)
            elif node.type == 'BOOL':
                return node.value == 'true'
            elif node.type == 'STRING':
                return node.value
            elif node.type == 'SYMBOL':
                return env.get(node.value)

        if not isinstance(node, list) or len(node) == 0:
            return None

        head = node[0]
        op = head.value if isinstance(head, Token) else None

        if op == 'fn':
            name = node[1].value
            params = [(p[0].value, p[1].value) for p in node[2]]
            ret_type = node[3].value
            body = node[4:]
            self.functions[name] = (params, ret_type, body)
            return None

        elif op == 'let':
            var_name = node[1].value
            val = self.eval(node[3], env)
            env.define(var_name, val)
            return val

        elif op == 'set':
            var_name = node[1].value
            val = self.eval(node[2], env)
            env.set(var_name, val)
            return val

        elif op == 'if':
            cond = self.eval(node[1], env)
            if cond:
                return self.eval(node[2], env)
            elif len(node) > 3:
                return self.eval(node[3], env)
            return None

        elif op == 'do':
            res = None
            for expr in node[1:]:
                res = self.eval(expr, env)
            return res

        elif op == 'loop':
            cond_expr = node[1]
            body = node[2:]
            res = None
            while self.eval(cond_expr, env):
                for expr in body:
                    res = self.eval(expr, env)
            return res

        elif op == 'for':
            var_name = node[1].value
            count = self.eval(node[2], env)
            body = node[3:]
            loop_env = NanoEnv(env)
            res = None
            for i in range(count):
                loop_env.define(var_name, i)
                for expr in body:
                    res = self.eval(expr, loop_env)
            return res

        elif op == 'call':
            fn_name = node[1].value
            if fn_name not in self.functions:
                raise NameError(f"Unknown function: {fn_name}")
            params, _, body = self.functions[fn_name]
            call_env = NanoEnv(self.global_env)
            for (pname, _), arg_node in zip(params, node[2:]):
                call_env.define(pname, self.eval(arg_node, env))
            try:
                res = None
                for expr in body:
                    res = self.eval(expr, call_env)
                return res
            except ReturnSignal as ret:
                return ret.value

        elif op == 'ret':
            val = self.eval(node[1], env) if len(node) > 1 else None
            raise ReturnSignal(val)

        elif op == 'println':
            vals = [str(self.eval(arg, env)) for arg in node[1:]]
            print(" ".join(vals))
            return None

        elif op == 'print':
            vals = [str(self.eval(arg, env)) for arg in node[1:]]
            print(" ".join(vals), end="")
            return None

        elif op in ('+', '-', '*', '/', '%', '==', '!=', '<', '<=', '>', '>='):
            left = self.eval(node[1], env)
            right = self.eval(node[2], env)
            ops = {
                '+': lambda a, b: a + b,
                '-': lambda a, b: a - b,
                '*': lambda a, b: a * b,
                '/': lambda a, b: a / b if isinstance(a, float) or isinstance(b, float) else a // b,
                '%': lambda a, b: a % b,
                '==': lambda a, b: a == b,
                '!=': lambda a, b: a != b,
                '<': lambda a, b: a < b,
                '<=': lambda a, b: a <= b,
                '>': lambda a, b: a > b,
                '>=': lambda a, b: a >= b,
            }
            return ops[op](left, right)

        elif op == 'and':
            return self.eval(node[1], env) and self.eval(node[2], env)
        elif op == 'or':
            return self.eval(node[1], env) or self.eval(node[2], env)
        elif op == 'not':
            return not self.eval(node[1], env)

        else:
            raise ValueError(f"Unknown operator or form: {op}")

    def run(self, ast: List[Any]):
        for stmt in ast:
            self.eval(stmt, self.global_env)
        if 'main' in self.functions:
            return self.eval([Token('SYMBOL', 'call', 0), Token('SYMBOL', 'main', 0)], self.global_env)

# ==========================================
# 3. NATIVE C99 CODE GENERATOR
# ==========================================

TYPE_MAP = {
    'i32': 'int32_t',
    'i64': 'int64_t',
    'f64': 'double',
    'bool': 'bool',
    'str': 'const char*',
    'void': 'void'
}

class C99Compiler:
    def __init__(self):
        pass

    def type_to_c(self, t: str) -> str:
        return TYPE_MAP.get(t, 'int32_t')

    def compile_expr(self, node: Any) -> str:
        if isinstance(node, Token):
            if node.type == 'INT':
                return node.value
            elif node.type == 'FLOAT':
                return node.value
            elif node.type == 'BOOL':
                return "1" if node.value == 'true' else "0"
            elif node.type == 'STRING':
                return f'"{node.value}"'
            elif node.type == 'SYMBOL':
                return node.value

        op = node[0].value
        if op in ('+', '-', '*', '/', '%', '==', '!=', '<', '<=', '>', '>='):
            return f"({self.compile_expr(node[1])} {op} {self.compile_expr(node[2])})"
        elif op == 'and':
            return f"({self.compile_expr(node[1])} && {self.compile_expr(node[2])})"
        elif op == 'or':
            return f"({self.compile_expr(node[1])} || {self.compile_expr(node[2])})"
        elif op == 'not':
            return f"(!{self.compile_expr(node[1])})"
        elif op == 'call':
            fn_name = node[1].value
            args = ", ".join(self.compile_expr(a) for a in node[2:])
            return f"{fn_name}({args})"
        elif op == 'if':
            return f"({self.compile_expr(node[1])} ? {self.compile_expr(node[2])} : {self.compile_expr(node[3])})"
        else:
            raise ValueError(f"Cannot compile {op} as an expression")

    def compile_stmt(self, node: Any, indent: int = 1, is_last_in_fn: bool = False) -> List[str]:
        pad = "    " * indent
        if not isinstance(node, list):
            expr_code = self.compile_expr(node)
            if is_last_in_fn:
                return [f"{pad}return {expr_code};"]
            return [f"{pad}{expr_code};"]

        op = node[0].value
        lines = []

        if op == 'let':
            vname = node[1].value
            ctype = self.type_to_c(node[2].value)
            init = self.compile_expr(node[3])
            lines.append(f"{pad}{ctype} {vname} = {init};")

        elif op == 'set':
            vname = node[1].value
            init = self.compile_expr(node[2])
            lines.append(f"{pad}{vname} = {init};")

        elif op == 'do':
            for idx, s in enumerate(node[1:]):
                is_sub_last = is_last_in_fn and (idx == len(node[1:]) - 1)
                lines.extend(self.compile_stmt(s, indent, is_sub_last))

        elif op == 'ret':
            if len(node) > 1:
                lines.append(f"{pad}return {self.compile_expr(node[1])};")
            else:
                lines.append(f"{pad}return;")

        elif op == 'if':
            cond = self.compile_expr(node[1])
            lines.append(f"{pad}if ({cond}) {{")
            lines.extend(self.compile_stmt(node[2], indent + 1, is_last_in_fn))
            if len(node) > 3:
                lines.append(f"{pad}}} else {{")
                lines.extend(self.compile_stmt(node[3], indent + 1, is_last_in_fn))
            lines.append(f"{pad}}}")

        elif op == 'loop':
            cond = self.compile_expr(node[1])
            lines.append(f"{pad}while ({cond}) {{")
            for stmt in node[2:]:
                lines.extend(self.compile_stmt(stmt, indent + 1, False))
            lines.append(f"{pad}}}")

        elif op == 'for':
            vname = node[1].value
            cnt = self.compile_expr(node[2])
            lines.append(f"{pad}for (int64_t {vname} = 0; {vname} < {cnt}; ++{vname}) {{")
            for stmt in node[3:]:
                lines.extend(self.compile_stmt(stmt, indent + 1, False))
            lines.append(f"{pad}}}")

        elif op in ('println', 'print'):
            fmt = []
            args = []
            for item in node[1:]:
                if isinstance(item, Token) and item.type == 'STRING':
                    fmt.append(item.value.replace("%", "%%"))
                else:
                    fmt.append("%lld")
                    args.append(f"(long long)({self.compile_expr(item)})")
            format_str = " ".join(fmt) + ("\\n" if op == 'println' else "")
            args_part = (", " + ", ".join(args)) if args else ""
            lines.append(f'{pad}printf("{format_str}"{args_part});')

        else:
            expr_code = self.compile_expr(node)
            if is_last_in_fn:
                lines.append(f"{pad}return {expr_code};")
            else:
                lines.append(f"{pad}{expr_code};")

        return lines

    def compile(self, ast: List[Any]) -> str:
        headers = [
            "#include <stdio.h>",
            "#include <stdint.h>",
            "#include <stdbool.h>",
            ""
        ]

        forward_decls = []
        fn_defs = []

        for node in ast:
            if isinstance(node, list) and node[0].value == 'fn':
                fn_name = node[1].value
                params = [(p[0].value, self.type_to_c(p[1].value)) for p in node[2]]
                ret_type = self.type_to_c(node[3].value)
                param_str = ", ".join(f"{ptype} {pname}" for pname, ptype in params) or "void"
                forward_decls.append(f"{ret_type} {fn_name}({param_str});")

                fn_body = [f"{ret_type} {fn_name}({param_str}) {{"]
                body_stmts = node[4:]
                for idx, stmt in enumerate(body_stmts):
                    is_last = (idx == len(body_stmts) - 1) and (ret_type != 'void')
                    fn_body.extend(self.compile_stmt(stmt, 1, is_last))
                fn_body.append("}\n")
                fn_defs.append("\n".join(fn_body))

        return "\n".join(headers + forward_decls + [""] + fn_defs)

# ==========================================
# 4. HUMAN VIEW PROJECTOR (Decompile to Python)
# ==========================================

class HumanProjector:
    """Projects dense AI-Native SYN-IR into clean, human-readable Python."""

    def project_expr(self, node: Any) -> str:
        if isinstance(node, Token):
            if node.type == 'BOOL':
                return 'True' if node.value == 'true' else 'False'
            elif node.type == 'STRING':
                return f'"{node.value}"'
            return node.value

        op = node[0].value
        if op in ('+', '-', '*', '/', '%', '==', '!=', '<', '<=', '>', '>='):
            return f"({self.project_expr(node[1])} {op} {self.project_expr(node[2])})"
        elif op == 'and':
            return f"({self.project_expr(node[1])} and {self.project_expr(node[2])})"
        elif op == 'or':
            return f"({self.project_expr(node[1])} or {self.project_expr(node[2])})"
        elif op == 'not':
            return f"(not {self.project_expr(node[1])})"
        elif op == 'call':
            fn_name = node[1].value
            args = ", ".join(self.project_expr(a) for a in node[2:])
            return f"{fn_name}({args})"
        elif op == 'if':
            return f"({self.project_expr(node[2])} if {self.project_expr(node[1])} else {self.project_expr(node[3])})"
        return f"{op}(...)"

    def project_stmt(self, node: Any, indent: int = 1, is_last: bool = False) -> List[str]:
        pad = "    " * indent
        if not isinstance(node, list):
            expr = self.project_expr(node)
            return [f"{pad}return {expr}" if is_last else f"{pad}{expr}"]

        op = node[0].value
        lines = []

        if op == 'fn':
            fn_name = node[1].value
            params = [f"{p[0].value}: {p[1].value}" for p in node[2]]
            ret_type = node[3].value
            lines.append(f"def {fn_name}({', '.join(params)}) -> {ret_type}:")
            body_stmts = node[4:]
            for idx, stmt in enumerate(body_stmts):
                lines.extend(self.project_stmt(stmt, indent, idx == len(body_stmts) - 1))
            lines.append("")

        elif op in ('let', 'set'):
            vname = node[1].value
            val = self.project_expr(node[3] if op == 'let' else node[2])
            lines.append(f"{pad}{vname} = {val}")

        elif op == 'do':
            for idx, s in enumerate(node[1:]):
                lines.extend(self.project_stmt(s, indent, is_last and (idx == len(node[1:]) - 1)))

        elif op == 'ret':
            if len(node) > 1:
                lines.append(f"{pad}return {self.project_expr(node[1])}")
            else:
                lines.append(f"{pad}return")

        elif op == 'if':
            lines.append(f"{pad}if {self.project_expr(node[1])}:")
            lines.extend(self.project_stmt(node[2], indent + 1, is_last))
            if len(node) > 3:
                lines.append(f"{pad}else:")
                lines.extend(self.project_stmt(node[3], indent + 1, is_last))

        elif op == 'loop':
            lines.append(f"{pad}while {self.project_expr(node[1])}:")
            for stmt in node[2:]:
                lines.extend(self.project_stmt(stmt, indent + 1, False))

        elif op == 'for':
            vname = node[1].value
            cnt = self.project_expr(node[2])
            lines.append(f"{pad}for {vname} in range({cnt}):")
            for stmt in node[3:]:
                lines.extend(self.project_stmt(stmt, indent + 1, False))

        elif op in ('println', 'print'):
            args = ", ".join(self.project_expr(a) for a in node[1:])
            lines.append(f"{pad}print({args})")

        elif op == 'call':
            lines.append(f"{pad}{self.project_expr(node)}")

        else:
            expr = self.project_expr(node)
            lines.append(f"{pad}return {expr}" if is_last else f"{pad}{expr}")

        return lines

    def project(self, ast: List[Any]) -> str:
        lines = ["# --- Projected Human-Auditable Python Code ---"]
        for node in ast:
            lines.extend(self.project_stmt(node, 0, False))
        return "\n".join(lines)

# ==========================================
# 5. CLI INTERFACE
# ==========================================

def main():
    if len(sys.argv) < 3:
        print("Usage: synapse.py <run|build|project|c-code> <file.syn> [output_binary]")
        sys.exit(1)

    cmd = sys.argv[1]
    filepath = sys.argv[2]

    with open(filepath, 'r') as f:
        src = f.read()

    tokens = tokenize(src)
    ast = parse_s_expr(tokens)

    if cmd == 'run':
        interpreter = NanoInterpreter()
        interpreter.run(ast)

    elif cmd == 'c-code':
        compiler = C99Compiler()
        c_code = compiler.compile(ast)
        print(c_code)

    elif cmd == 'build':
        out_bin = sys.argv[3] if len(sys.argv) > 3 else filepath.replace('.syn', '')
        compiler = C99Compiler()
        c_code = compiler.compile(ast)
        with tempfile.NamedTemporaryFile('w', suffix='.c', delete=False) as c_file:
            c_file.write(c_code)
            c_file_path = c_file.name

        try:
            cmd_build = ["clang", "-O3", c_file_path, "-o", out_bin]
            res = subprocess.run(cmd_build, capture_output=True, text=True)
            if res.returncode != 0:
                print("Compilation error:", res.stderr)
                sys.exit(1)
            print(f"[Synapse] Successfully compiled to native binary: {out_bin}")
        finally:
            os.remove(c_file_path)

    elif cmd == 'project':
        projector = HumanProjector()
        print(projector.project(ast))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == '__main__':
    main()
