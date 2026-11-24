---
name: java-repair
description: Repair a Java bug from failing tests or a stack trace. Use when the task is "fix this bug", "make the failing test pass", or when a stack trace points into this repository.
allowed-tools: [read_file, search_code, run_tests, edit_file, bash, finish]
version: 1.0
---

# Java repair

## Workflow

1. **Reproduce.** Run the failing test (or the module's suite) before touching code.
2. **Locate.** Start at the top stack frame that belongs to this repository; read that
   method and its callers before reading unrelated files.
3. **Hypothesis.** Write one sentence: "if X is true, the test fails". Then check X.
4. **Minimal fix.** Change the smallest amount of production code. Do not refactor
   adjacent methods, reformat files, or rename things.
5. **Regress.** Run the suite again. Any previously passing test that now fails means
   the fix is wrong, not that the test is wrong.
6. **Deliver.** Summarise root cause, the change, and the risks in finish(summary).

## Anti-patterns

- Editing tests, assertions, or build files to make a run green.
- Catching and swallowing exceptions to hide a failure.
- Hard-coding the value a test expects.
- Rewriting a whole file when two lines would do.
- Reading dozens of files before forming a hypothesis.

## When the suite is slow

Run the single failing test first, then the module suite, then everything.
Batch edits before running tests; each run costs a minute or more.
