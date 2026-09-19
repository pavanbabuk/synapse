# Synapse (SYN-IR) ⚡
> **An AI-Native Language & Verified Execution Spine.**
> Guarantees deterministic artifacts, emits structured machine-readable repair plans, cuts host RAM by **89%**, and executes **22x faster than Python** via freestanding compilation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/pavanbabuk/synapse/actions/workflows/ci.yml/badge.svg)](https://github.com/pavanbabuk/synapse/actions)
[![Status: Experimental Alpha](https://img.shields.io/badge/Status-Experimental%20Alpha%20v0.2.0-orange.svg)](#)
[![Memory: <2MB RAM](https://img.shields.io/badge/RAM-1.58MB-green.svg)](#)

---

## 💡 The Thesis: Beyond Human Syntactic Fluff

Languages like Python, TypeScript, and Rust were engineered around **human visual and cognitive constraints**:
* Indentation sensitivity and complex operator precedence create hallucination traps for LLMs.
* Tracing garbage collectors and dynamic runtimes consume tens of megabytes of RAM and induce stop-the-world pauses.
* Compiler diagnostics formatted for human eyes (colored text, wavy underlines) force AI coding agents to waste valuable context simulating fixes.

**Synapse is built ground-up for autonomous AI agents and ultra-low-resource hardware:**
1. **Deterministic Artifacts**: S-expression ASTs enforce explicit evaluation order with zero precedence or scoping ambiguities.
2. **Compiler-as-Assistant (`syn check`)**: The compiler outputs structured JSON repair plans directly consumable by LLM self-healing loops.
3. **Freestanding Native Execution**: Compiles via `clang -O3` into standalone machine code requiring **under 1.6 MB RAM** with **zero runtime engine dependencies**.
4. **Bi-Directional Python Interop**: Audited transpilation between pure Python logic and Synapse IR.

---

## 🤖 Compiler-as-Assistant: Structured Machine Repair

When an AI agent makes an error, traditional compilers emit human text that requires multi-turn guessing. Synapse emits machine-readable AST patch plans:

```bash
$ syn check faulty_agent_output.syn
```

```json
{
  "diagnostics": [
    {
      "status": "error",
      "error_type": "undefined_variable",
      "function": "process_items",
      "target": "total",
      "message": "Variable 'total' is mutated before being declared.",
      "repair_plan": {
        "action": "insert_declaration",
        "suggested_fix": "(let total i32 0)"
      }
    }
  ],
  "count": 1
}
```
*Agents like Devin, Cursor, and Claude can parse this envelope and patch their generated AST in a single turn.*

---

## 📊 Performance & Host Resource Footprint

Tested on a 500,000 prime computation benchmark:

| Metric | Standard Python 3.x | Synapse Native Binary | Advantage |
| :--- | :--- | :--- | :--- |
| **Execution Time** | `506.08 ms` | `22.46 ms` | **22.5x Faster** 🚀 |
| **Peak Memory (RAM)** | `14.39 MB` | `1.59 MB` | **88.9% Less RAM** 💾 |
| **Runtime Overhead** | Python VM + Tracing GC | Standalone Freestanding Binary | **Zero Engine Overhead** |
| **Self-Healing Loop**| Text-based error logs | Structured JSON Repair AST | **1-Turn Agent Healing** |

---

## 🔌 Python Compatibility Matrix

Synapse provides an explicit, honest compatibility contract for Python code (`py2syn`):

| Category | Features | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Primitives** | `int`, `float`, `bool`, `str`, `void` | ✅ 100% Supported | Directly mapped to fixed C99 types |
| **Control Flow** | `if/elif/else`, `while`, `for i in range(...)` | ✅ 100% Supported | Desugared into pure branching AST |
| **Functions** | Type annotations, recursion, scoped variables | ✅ 100% Supported | Fully supported |
| **Memory** | Stack variables, bounded arrays | ✅ Supported | Managed with zero garbage collection |
| **Dynamic Python** | `eval()`, `exec()`, monkey-patching | ❌ Explicit Non-Goal | Incompatible with deterministic safety |

---

## 🚀 Quick Start

### 1. Unified CLI (`syn`)

```bash
# Run self-repair linter (emits JSON diagnostic envelope)
./bin/syn check examples/prime_counter.syn

# Compile Python or Synapse into a freestanding machine binary
./bin/syn build examples/math_lib.py ./native_math
./native_math

# Project Synapse IR back to readable Python for human audit
./bin/syn project examples/fibonacci.syn

# Run performance & memory benchmarks
./bin/syn bench
```

---

## 🧠 LLM Agent Context Package

Synapse includes ready-to-use artifacts for LLM agent prompt contexts:
* **[`SYNAPSE_CONTEXT.json`](SYNAPSE_CONTEXT.json)**: Machine-readable schema, grammar rules, and canonical one-shot examples.
* **[`MEMORY.md`](MEMORY.md)**: System prompt instructions for autonomous agents.

---

## 📜 License
MIT License. Open for researchers, AI agents, and systems engineers.
