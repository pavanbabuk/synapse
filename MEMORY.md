# Synapse Agent Memory & Grammar Guide

This file provides autonomous AI coding agents (Devin, Claude, Cursor, AutoGen) with instant, infallible context on how to construct, audit, and patch Synapse code.

---

## 1. Syntax Invariants
1. **Always use parentheses for every expression**:
   - `(+ a b)` NOT `a + b`
   - `(call fn_name arg1 arg2)` NOT `fn_name(arg1, arg2)`
2. **Block Evaluation with `do`**:
   - Inside `if`, `for`, or `loop`, group multi-step actions using `(do ...)`:
   ```lisp
   (if (> x 0)
     (do
       (set x (- x 1))
       (println "Decremented"))
     (do
       (println "Zero reached")))
   ```
3. **Variable Lifecycle**:
   - Declare with `(let <var> <type> <val>)`.
   - Mutate with `(set <var> <val>)`.
   - Available primitive types: `i32`, `i64`, `f64`, `bool`, `str`, `void`.

---

## 2. Compiler Self-Repair Loop
When the compiler encounters an issue, invoke:
```bash
syn check <file.syn> --json-repair
```
The output will be structured JSON specifying:
- `error_type`: (e.g. `undefined_variable`, `type_mismatch`, `syntax_error`)
- `line`: The exact line of failure
- `suggested_patch`: The AST node replacement plan

Use this patch plan directly to modify your generated code without hallucinating arbitrary refactors.
