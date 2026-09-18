# Synapse (SYN-IR) ⚡
> **An AI-Native, Ultra-Low-Resource Programming Language & Execution Engine.**
> Cuts RAM by **89%**, runs **22x faster than Python**, and eliminates LLM syntax hallucinations through a deterministic S-Expression AST.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Language: AI-Native](https://img.shields.io/badge/Language-AI--Native-blue.svg)](#)
[![Memory: <2MB RAM](https://img.shields.io/badge/RAM-1.58MB-green.svg)](#)

---

## 💡 Why Synapse?

Every mainstream programming language today (Python, Rust, C++, JavaScript) was designed around **human visual and cognitive constraints**:
* **Whitespace and indentation traps** (Python) cause LLMs to make subtle scoping and indentation errors.
* **Complex syntactic sugar and operator precedence** burn up expensive tokens and prompt context.
* **Heavy runtimes and tracing garbage collectors** (Python, Node.js, Go, Java) eat tens of megabytes of RAM and induce unpredictable GC pauses.

**Synapse is built from the ground up for the AI era:**
1. **Zero-Ambiguity Prefix AST (`.syn`)**: Mathematical S-expressions eliminate operator precedence and indentation bugs entirely.
2. **Freestanding Native Execution**: Compiles via `clang -O3` into standalone machine code requiring **under 1.6 MB RAM** and **zero runtime dependencies**.
3. **Bi-Directional Python Bridge**:
   * **`Python -> Synapse`**: Automatically convert pure Python libraries and functions into Synapse IR.
   * **`Synapse -> Python`**: Instantly project machine-oriented `.syn` back into clean, auditable Python for human code review.

---

## 📊 Live Benchmark (500,000 Prime Number Computations)

| Metric | Standard Python 3.x | Synapse Native Binary | Advantage |
| :--- | :--- | :--- | :--- |
| **Execution Time** | `506.08 ms` | `22.46 ms` | **22.5x Faster** 🚀 |
| **Peak Memory (RAM)** | `14.39 MB` | `1.59 MB` | **88.9% Less RAM** 💾 |
| **Runtime Overhead** | Python VM + GC Heap | Standalone Machine Code | **Freestanding** |
| **LLM Syntax Safety**| Indentation-sensitive | Deterministic S-AST | **Zero Ambiguity** |

---

## 🛠️ Architecture

```
                 ┌──────────────────────────────────────┐
                 │          Human / AI Input            │
                 │   Python code (.py) or SYN-IR (.syn) │
                 └──────────────────┬───────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
          [ py2syn Transpiler ]               [ Synapse Parser ]
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
                 ┌──────────────────────────────────────┐
                 │       Synapse Intermediate AST       │
                 │   - Linear memory / No GC            │
                 │   - Scoped stack execution           │
                 └──────────┬───────────────────┬───────┘
                            │                   │
               ┌────────────┴───────┐           └──────────────┐
               ▼                    ▼                          ▼
     ┌──────────────────┐  ┌──────────────────┐    ┌───────────────────────┐
     │  Native Clang    │  │  Nano Micro-VM   │    │  Human Projector      │
     │  Freestanding C  │  │  Instant eval    │    │  Decompile to clean   │
     │  Binary (<2MB)   │  │  (<500KB RAM)    │    │  readable Python      │
     └──────────────────┘  └──────────────────┘    └───────────────────────┘
```

---

## 🚀 Quick Start

### 1. Requirements
* Python 3.8+ (for compiler tooling)
* `clang` or `gcc` (for freestanding native binary compilation)

### 2. Basic Commands with the Unified CLI (`syn`)

```bash
# Run a Synapse program in the instant nano-interpreter
./bin/syn run examples/prime_counter.syn

# Compile directly to a standalone native binary
./bin/syn build examples/fibonacci.syn ./fib_bin
./fib_bin

# Automatically transpile and run a Python library as native machine code!
./bin/syn build examples/math_lib.py ./native_math
./native_math

# Decompile / Project Synapse IR back into human-readable Python
./bin/syn project examples/prime_counter.syn

# Run the comparative benchmark
./bin/syn bench
```

---

## 📝 Synapse Code Example

```lisp
;; Fibonacci in Synapse IR
(fn fib ((n i32)) i32
  (if (<= n 1)
    (ret n)
    (ret (+ (call fib (- n 1))
            (call fib (- n 2))))))

(fn main () i32
  (let res i32 (call fib 20))
  (println "Fibonacci(20) =" res)
  (ret 0))
```

---

## 🤖 Prompting LLMs to Write Synapse

You can instruct any modern LLM (ChatGPT, Claude, Gemini) to generate Synapse code using this zero-shot system instruction:

> *"Generate logic in Synapse S-Expression IR. Rules: (fn name ((arg type)) ret_type ...), (let var type val), (set var val), (if cond (do then...) (do else...)), (for i count ...), (loop cond ...), (ret val). Use types: i32, f64, bool, str."*

---

## 📜 License
MIT License. Open for researchers, AI agents, and embedded systems developers.
