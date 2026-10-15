# Working rules for this project

- The user writes all physics implementations. Claude explains and reviews code but never implements physics functions (compressible-flow relations, shock relations, geometry solvers, etc.) — only stubs with docstrings, or tests/tooling/scaffolding.
- Never invent reference values. Any numeric value sourced from NACA Report 1135 or another reference must be marked `# VERIFY: <source, table/chart>` and the corresponding test marked `@pytest.mark.skip(reason="reference value not verified")` until the user confirms the value.
- One task per session. End each session with a green `pytest` run (skips are fine; failures and errors are not).
- Use plan mode for any change that touches more than 2 files.
- When tests pass, suggest a commit message — do not commit automatically.
