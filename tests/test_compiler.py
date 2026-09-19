#!/usr/bin/env python3
"""
Synapse Compiler & Runtime Test Suite.
Tests:
1. Tokenizer & Parser correctness (nested expressions, strings, numbers)
2. Nano-interpreter execution
3. Native C99 Clang compilation and standalone execution
4. Linter & self-repair diagnostics (negative tests)
5. Python-to-Synapse transpilation round-trip
"""

import sys
import os
import unittest
import subprocess
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from synapse import tokenize, parse_s_expr, NanoInterpreter, C99Compiler, Linter
from py2syn import transpile

class TestTokenizerParser(unittest.TestCase):
    def test_tokenize_basic(self):
        code = '(fn add ((a i32) (b i32)) i32 (+ a b))'
        tokens = tokenize(code)
        self.assertEqual(tokens[0].type, 'LPAREN')
        self.assertEqual(tokens[1].value, 'fn')
        self.assertEqual(tokens[-1].type, 'RPAREN')

    def test_tokenize_string_literal(self):
        code = '(println "hello world")'
        tokens = tokenize(code)
        self.assertEqual(tokens[2].type, 'STRING')
        self.assertEqual(tokens[2].value, 'hello world')

    def test_parse_nested_ast(self):
        code = '(+ (* 2 3) (/ 10 2))'
        tokens = tokenize(code)
        ast = parse_s_expr(tokens)
        self.assertEqual(len(ast), 1)
        root = ast[0]
        self.assertEqual(root[0].value, '+')
        self.assertEqual(root[1][0].value, '*')
        self.assertEqual(root[2][0].value, '/')

class TestInterpreterExecution(unittest.TestCase):
    def test_arithmetic_eval(self):
        code = '''
        (fn main () i32
          (let x i32 15)
          (let y i32 25)
          (ret (+ x y)))
        '''
        ast = parse_s_expr(tokenize(code))
        interp = NanoInterpreter()
        res = interp.run(ast)
        self.assertEqual(res, 40)

    def test_loop_and_conditionals(self):
        code = '''
        (fn main () i32
          (let sum i32 0)
          (for i 10
            (if (== (% i 2) 0)
              (set sum (+ sum i))
              0))
          (ret sum))
        '''
        ast = parse_s_expr(tokenize(code))
        interp = NanoInterpreter()
        res = interp.run(ast)
        # 0 + 2 + 4 + 6 + 8 = 20
        self.assertEqual(res, 20)

class TestNativeClangCompilation(unittest.TestCase):
    def test_native_build_and_run(self):
        code = '''
        (fn factorial ((n i32)) i32
          (if (<= n 1)
            (ret 1)
            (ret (* n (call factorial (- n 1))))))

        (fn main () i32
          (let ans i32 (call factorial 5))
          (println ans)
          (ret 0))
        '''
        ast = parse_s_expr(tokenize(code))
        compiler = C99Compiler()
        c_code = compiler.compile(ast)

        with tempfile.NamedTemporaryFile('w', suffix='.c', delete=False) as c_file:
            c_file.write(c_code)
            c_file_path = c_file.name

        out_bin = tempfile.mktemp(prefix="syn_test_bin_")

        try:
            # Compile with Clang and AddressSanitizer for memory safety verification
            cmd_build = ["clang", "-O2", "-fsanitize=address", c_file_path, "-o", out_bin]
            res = subprocess.run(cmd_build, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Clang build failed: {res.stderr}")

            # Run binary
            res_run = subprocess.run([out_bin], capture_output=True, text=True)
            self.assertEqual(res_run.returncode, 0)
            self.assertEqual(res_run.stdout.strip(), "120")
        finally:
            if os.path.exists(c_file_path):
                os.remove(c_file_path)
            if os.path.exists(out_bin):
                os.remove(out_bin)

class TestLinterAndSelfRepair(unittest.TestCase):
    def test_undefined_variable_detection(self):
        code = '''
        (fn test () i32
          (set undeclared_x 100)
          (ret 0))
        '''
        ast = parse_s_expr(tokenize(code))
        linter = Linter()
        diags = linter.check(ast)
        self.assertTrue(len(diags) > 0)
        self.assertEqual(diags[0]["error_type"], "undefined_variable")
        self.assertEqual(diags[0]["target"], "undeclared_x")
        self.assertIn("repair_plan", diags[0])

    def test_clean_code_passes_linter(self):
        code = '''
        (fn add ((a i32) (b i32)) i32
          (let c i32 (+ a b))
          (ret c))
        '''
        ast = parse_s_expr(tokenize(code))
        linter = Linter()
        diags = linter.check(ast)
        self.assertEqual(len(diags), 0)

class TestPythonTranspiler(unittest.TestCase):
    def test_py2syn_transpilation(self):
        py_code = '''
def calculate(n: int) -> int:
    acc = 0
    for i in range(n):
        acc += i
    return acc
'''
        syn_code = transpile(py_code)
        self.assertIn("(fn calculate ((n i32)) i32", syn_code)
        self.assertIn("(for i n", syn_code)
        self.assertIn("(set acc (+ acc i))", syn_code)

        # Ensure generated Synapse parses without errors
        ast = parse_s_expr(tokenize(syn_code))
        self.assertTrue(len(ast) > 0)

if __name__ == '__main__':
    unittest.main()
