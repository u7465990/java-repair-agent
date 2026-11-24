---
name: maven-diagnostics
description: Diagnose Maven and Ant build failures. Use when compilation fails, dependencies are missing, or the build behaves differently from the test run.
allowed-tools: [read_file, search_code, bash, run_tests]
version: 1.0
---

# Build diagnostics

## First checks

1. Read the exact compiler error: file, line, symbol. Fix the first error before the rest.
2. `mvn -o -q -DskipTests compile` reproduces compilation without network.
3. `mvn -X` prints the effective classpath and plugin versions when resolution looks wrong.

## Common causes

| Symptom | Likely cause |
|---|---|
| `cannot find symbol` | missing import, wrong overload, or a method removed by the change |
| `package does not exist` | dependency scope or a missing module build |
| tests compile but fail to start | surefire/JUnit version mismatch |
| works locally, fails in sandbox | offline mode with a missing local repository entry |

## Rules

- Do not edit `pom.xml` or `build.xml` in a repair patch; treat build changes as a separate task.
- If the offline build lacks an artifact, report it instead of guessing a version.
- Prefer the project's existing build command over inventing a new one.
