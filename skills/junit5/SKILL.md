---
name: junit5
description: Write or adjust JUnit 5 tests. Use when a task involves adding a regression test, fixing test compilation, or understanding an assertion failure.
allowed-tools: [read_file, edit_file, run_tests]
version: 1.0
---

# JUnit 5

## Writing a test

- One behaviour per test; the name should state the expected outcome.
- Prefer `assertThrows`, `assertEquals` with a message, and `assertAll` for grouped checks.
- Use `@ParameterizedTest` with `@ValueSource` / `@CsvSource` instead of copy-pasted tests.
- Use `@TempDir` for filesystem tests; never write into the repository root.
- Avoid `Thread.sleep`; use `assertTimeoutPreemptively` only for real concurrency checks.

## Reading a failure

1. The first line is the assertion message; the second is the expected/actual pair.
2. The first stack frame inside this project is usually the production method to inspect.
3. A `NullPointerException` in a test often means a fixture was not initialised, not that production code is wrong.

## Rules

- Do not weaken assertions to make a test pass.
- Do not delete a failing test; fix the production code or the fixture.
- Keep test edits out of repair patches unless the task explicitly asks for a test.
