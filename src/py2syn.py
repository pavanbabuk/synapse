#!/usr/bin/env python3
"""
py2syn: Python-to-Synapse AST Transpiler.
Translates pure Python functions into ultra-low-resource Synapse (SYN-IR).
"""

import ast
import sys

TYPE_MAP = {
    'int': 'i32',
    'float': 'f64',
    'bool': 'bool',
    'str': 'str',
    'None': 'void'
}

class PythonToSynapse(ast.NodeVisitor):
    def __init__(self):
        self.declared_vars = set()

    def translate_type(self, node) -> str:
        if node is None:
            return 'i32'
        if isinstance(node, ast.Name):
            return TYPE_MAP.get(node.id, 'i32')
        elif isinstance(node, ast.Constant):
            return TYPE_MAP.get(str(node.value), 'i32')
        return 'i32'

    def visit_Module(self, node) -> str:
        chunks = []
        for stmt in node.body:
            code = self.visit(stmt)
            if code:
                chunks.append(code)
        return "\n\n".join(chunks)

    def visit_FunctionDef(self, node) -> str:
        fn_name = node.name
        self.declared_vars = set()

        # Parse parameters
        params = []
        for arg in node.args.args:
            pname = arg.arg
            ptype = self.translate_type(arg.annotation)
            params.append(f"({pname} {ptype})")
            self.declared_vars.add(pname)
        param_str = f"({' '.join(params)})"

        # Return type
        ret_type = self.translate_type(node.returns)

        # Body statements
        body_lines = []
        for stmt in node.body:
            res = self.visit(stmt)
            if res:
                body_lines.append(res)

        formatted_body = "\n  ".join(body_lines)
        return f"(fn {fn_name} {param_str} {ret_type}\n  {formatted_body})"

    def visit_Return(self, node) -> str:
        if node.value is None:
            return "(ret)"
        val = self.visit(node.value)
        return f"(ret {val})"

    def visit_Assign(self, node) -> str:
        # e.g. x = 10
        target = node.targets[0]
        if isinstance(target, ast.Name):
            vname = target.id
            val = self.visit(node.value)
            if vname in self.declared_vars:
                return f"(set {vname} {val})"
            else:
                self.declared_vars.add(vname)
                # Default type inference
                vtype = 'f64' if isinstance(node.value, ast.Constant) and isinstance(node.value.value, float) else 'i32'
                return f"(let {vname} {vtype} {val})"
        return ";; Unsupported assignment"

    def visit_AugAssign(self, node) -> str:
        # e.g. x += 1
        if isinstance(node.target, ast.Name):
            vname = node.target.id
            val = self.visit(node.value)
            op = self.get_op_symbol(node.op)
            return f"(set {vname} ({op} {vname} {val}))"
        return ";; Unsupported aug-assign"

    def visit_If(self, node) -> str:
        test = self.visit(node.test)
        then_body = "\n    ".join(self.visit(s) for s in node.body)
        if node.orelse:
            else_body = "\n    ".join(self.visit(s) for s in node.orelse)
            return f"(if {test}\n    (do\n      {then_body})\n    (do\n      {else_body}))"
        else:
            return f"(if {test}\n    (do\n      {then_body})\n    0)"

    def visit_While(self, node) -> str:
        test = self.visit(node.test)
        body = "\n    ".join(self.visit(s) for s in node.body)
        return f"(loop {test}\n    {body})"

    def visit_For(self, node) -> str:
        # Handles for i in range(count):
        if isinstance(node.target, ast.Name) and isinstance(node.iter, ast.Call):
            vname = node.target.id
            self.declared_vars.add(vname)
            func = node.iter.func
            if isinstance(func, ast.Name) and func.id == 'range':
                if len(node.iter.args) == 1:
                    cnt = self.visit(node.iter.args[0])
                    body = "\n    ".join(self.visit(s) for s in node.body)
                    return f"(for {vname} {cnt}\n    {body})"
        return ";; Unsupported for loop"

    def visit_Expr(self, node) -> str:
        return self.visit(node.value)

    def visit_Call(self, node) -> str:
        if isinstance(node.func, ast.Name):
            fname = node.func.id
            if fname == 'print':
                args = " ".join(self.visit(a) for a in node.args)
                return f"(println {args})"
            else:
                args = " ".join(self.visit(a) for a in node.args)
                return f"(call {fname} {args})" if args else f"(call {fname})"
        return ";; Unsupported call"

    def visit_BinOp(self, node) -> str:
        op = self.get_op_symbol(node.op)
        left = self.visit(node.left)
        right = self.visit(node.right)
        return f"({op} {left} {right})"

    def visit_Compare(self, node) -> str:
        left = self.visit(node.left)
        op = self.get_cmp_symbol(node.ops[0])
        right = self.visit(node.comparators[0])
        return f"({op} {left} {right})"

    def visit_Constant(self, node) -> str:
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        elif isinstance(node.value, str):
            return f'"{node.value}"'
        return str(node.value)

    def visit_Name(self, node) -> str:
        return node.id

    def get_op_symbol(self, op) -> str:
        if isinstance(op, ast.Add): return '+'
        if isinstance(op, ast.Sub): return '-'
        if isinstance(op, ast.Mult): return '*'
        if isinstance(op, ast.Div): return '/'
        if isinstance(op, ast.Mod): return '%'
        return '+'

    def get_cmp_symbol(self, op) -> str:
        if isinstance(op, ast.Eq): return '=='
        if isinstance(op, ast.NotEq): return '!='
        if isinstance(op, ast.Lt): return '<'
        if isinstance(op, ast.LtE): return '<='
        if isinstance(op, ast.Gt): return '>'
        if isinstance(op, ast.GtE): return '>='
        return '=='

def transpile(python_source: str) -> str:
    tree = ast.parse(python_source)
    visitor = PythonToSynapse()
    return visitor.visit(tree)

def main():
    if len(sys.argv) < 2:
        print("Usage: py2syn.py <input.py> [output.syn]")
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else in_file.replace('.py', '.syn')

    with open(in_file, 'r') as f:
        py_src = f.read()

    syn_code = transpile(py_src)

    if len(sys.argv) > 2:
        with open(out_file, 'w') as f:
            f.write(syn_code)
        print(f"[py2syn] Successfully transpiled {in_file} -> {out_file}")
    else:
        print(syn_code)

if __name__ == '__main__':
    main()
