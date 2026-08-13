# calculator

A small **console calculator** written in Python. It evaluates arithmetic
expressions that use only:

* `+` — addition
* `-` — subtraction (both binary `a - b` and unary `-a`)
* `(` `)` — parentheses for grouping

Numbers may be integers or decimals. Everything else is rejected with a clear
error message.

```
(1 + 2) - -3   ->  6
10 - (3 - 2)   ->  9
-(4 - 9)       ->  5
```

## Requirements

* [uv](https://docs.astral.sh/uv/) (0.12+) — manages the Python version,
  the virtual environment and dependencies.
* Python 3.10+ (uv will fetch it for you if needed).

## Setup

From this directory (`calculator/`):

```bash
uv sync
```

This creates a `.venv`, installs the package in editable mode, and installs the
test dependency (pytest).

## Running the calculator

**Interactive REPL** — start it and type expressions:

```bash
uv run calculator
```

```
calc> 1 + 2
3
calc> (10 - 4) - -1
7
calc> quit
```

Exit with `quit`, `exit`, or `Ctrl-D`.

**One-shot** — pass the expression as arguments and get the result on stdout
(handy for scripts; exits non-zero on a bad expression):

```bash
uv run calculator "(1 + 2) - -3"      # -> 6
```

**As a module** — equivalent to the script entry point:

```bash
uv run python -m calculator "10 - (3 - 2)"   # -> 9
```

**From Python:**

```python
from calculator import Calculator, calculate

Calculator().evaluate("1 + (2 - 3)")   # -> 0
calculate("-(4 - 9)")                  # -> 5
```

## Running the tests

```bash
uv run pytest
```

The suite covers each stage in isolation plus end-to-end behavior:

| File                     | What it covers                                  |
| ------------------------ | ----------------------------------------------- |
| `tests/test_tokenizer.py`| numbers, operators, whitespace, bad characters  |
| `tests/test_parser.py`   | AST shape, associativity, grouping, syntax errors |
| `tests/test_evaluator.py`| full expressions and their numeric results      |
| `tests/test_cli.py`      | REPL loop and one-shot exit codes               |

## Project structure

```
calculator/
├── pyproject.toml              # project metadata, script entry, pytest config
├── README.md                   # this guide
├── src/
│   └── calculator/
│       ├── __init__.py         # public API: Calculator, calculate
│       ├── __main__.py         # enables `python -m calculator`
│       ├── cli.py              # REPL + one-shot entry point
│       ├── core.py             # Calculator facade (tokenize -> parse -> eval)
│       ├── tokenizer.py        # Tokenizer: text -> tokens
│       ├── tokens.py           # Token / TokenType definitions
│       ├── parser.py           # Parser: tokens -> AST
│       ├── ast_nodes.py        # Expr nodes + visitor interface
│       ├── evaluator.py        # Evaluator: AST -> number
│       └── errors.py           # CalculatorError hierarchy
└── tests/
    ├── test_tokenizer.py
    ├── test_parser.py
    ├── test_evaluator.py
    └── test_cli.py
```

## How it works

Turning a string like `"1 + (2 - 3)"` into the number `0` happens in **three
stages**, each a separate class with a single job (a classic OOP interpreter
design). Splitting it this way keeps every stage simple and independently
testable — which is exactly why there is one test file per stage.

```
"1 + (2 - 3)"  ──Tokenizer──►  [tokens]  ──Parser──►  AST tree  ──Evaluator──►  0
     text                       flat list             structure                number
```

Grammar (`+`/`-` only, left-associative, with parentheses):

```
expression := unary (('+' | '-') unary)*
unary      := ('+' | '-') unary | primary
primary    := NUMBER | '(' expression ')'
```

### Tokenizer vs. Parser

These two are easy to confuse, so here is the distinction:

The **Tokenizer** (`tokenizer.py`) works at the level of **characters**. It
scans the string left-to-right, discards whitespace, and groups characters into
"words" called *tokens*. It answers only "what are the pieces?" — it has no
opinion on whether they make sense in that order:

```
"1 + (2 - 3)"  →  [NUMBER(1), PLUS, LPAREN, NUMBER(2), MINUS, NUMBER(3), RPAREN, EOF]
```

Its only notion of "wrong" is a character it cannot classify at all — e.g. `*`
raises `TokenizeError`. Note that `"1 + )"` tokenizes just fine.

The **Parser** (`parser.py`) works at the level of **tokens**. It checks that
the token sequence forms a *grammatically valid* expression and builds a tree
capturing its structure (what groups with what). This is where `"1 + )"` fails
with a `ParseError`, and where the grammar rules — left-associativity, how
parentheses group — are enforced.

An analogy with English: the tokenizer splits a sentence into words
(`"the cat sat"` → `["the", "cat", "sat"]`), while the parser checks the grammar
and works out subject/verb/object. `"cat the sat"` is made of valid words but is
not a valid sentence — rejecting that is the parser's job.

### What is an AST?

**AST** stands for **Abstract Syntax Tree** — the tree-shaped representation of
the expression that the parser produces (defined in `ast_nodes.py`). A flat
token list is just a sequence; it does not capture *nesting* or *precedence*. A
tree does. For `"1 + (2 - 3)"`:

```
        BinaryOp("+")
        /          \
   Number(1)    BinaryOp("-")
                 /         \
            Number(2)   Number(3)
```

The structure is now explicit and unambiguous: "add `1` to the result of
subtracting `3` from `2`." The parentheses from the original text are *gone* —
they did their job (forcing that grouping) and the tree encodes the grouping
directly. That is the "abstract" in Abstract Syntax Tree: it keeps the meaning
and drops the surface syntax (parentheses, whitespace). The tree is built from
three node types: `Number` (a leaf), `UnaryOp` (one operator, one child) and
`BinaryOp` (one operator, two children).

### What is the Evaluator?

The **Evaluator** (`evaluator.py`) walks the AST and computes the actual number.
For the tree above it works bottom-up: evaluate `2 - 3` → `-1`, then
`1 + (-1)` → `0`.

It uses the **visitor pattern**: each node has an `accept()` method, and the
evaluator provides `visit_number` / `visit_unary` / `visit_binary`. Keeping the
evaluator separate from the nodes is deliberate separation of concerns — the
nodes describe only *structure*, while the evaluator is one *operation over* that
structure. A new operation (a formatter that turns the tree back into text, a
constant-folding optimizer, …) is just another visitor, added without touching
the node classes.
