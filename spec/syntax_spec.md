# Synapse (SYN-IR) Language Specification v0.1

Synapse is an **AI-native, deterministic, low-resource intermediate programming language**.
It eliminates human syntactic sugar (such as ambiguous operator precedence, indentation rules, and complex keyword variants) in favor of a dense, unambiguous **S-expression Abstract Syntax Tree (S-AST)**.

---

## 1. Design Principles

1. **Deterministic Syntax for AI**:
   - Every expression is an explicit S-expression: `(op arg1 arg2 ...)`.
   - Zero syntactic ambiguity: LLMs cannot make operator precedence or indentation errors.
   - 30-50% fewer tokens required to represent complex logic compared to Python, C++, or Rust.

2. **Ultra-Low Resource Consumption**:
   - **No Garbage Collector (GC)**: Memory is managed via strictly bounded stack allocations and linear scoped arenas.
   - **Deterministic Footprint**: Programs can run with less than **500 KB of RAM**.
   - **Zero Cold-Start Latency**: Compiles directly to freestanding C99 / machine code or runs via a nano-interpreter in microseconds.

3. **Dual-Layer Transparency**:
   - AI generates and optimizes `.syn`.
   - Human auditing tools project `.syn` into idiomatic, readable Python/pseudo-code on demand.

---

## 2. Core Types

| Type | Description | C Representation |
| :--- | :--- | :--- |
| `i32` | 32-bit signed integer | `int32_t` |
| `i64` | 64-bit signed integer | `int64_t` |
| `f64` | 64-bit floating point | `double` |
| `bool`| Boolean (`true` or `false`) | `bool` / `uint8_t` |
| `str` | Immutable string slice | `const char*` |
| `void`| Unit / No return | `void` |

---

## 3. Core Forms (Grammar)

### A. Function Definition
```lisp
(fn name ((param1 type1) (param2 type2)) return_type
  body_expr...)
```

### B. Variables & Binding
```lisp
(let var_name type initial_value)
(set var_name new_value)
```

### C. Conditionals
```lisp
(if condition
  then_expr
  else_expr)
```

### D. Iteration & Loops
```lisp
;; While-style loop
(loop condition
  body_expr...)

;; Range-based loop (0 to N-1)
(for var_name count
  body_expr...)
```

### E. Arithmetic and Logic
```lisp
(+ a b)
(- a b)
(* a b)
(/ a b)
(% a b)
(== a b)
(!= a b)
(< a b)
(<= a b)
(> a b)
(>= a b)
(and a b)
(or a b)
(not a)
```

### F. Output
```lisp
(println expr...)
(print expr...)
(ret expr)
```
