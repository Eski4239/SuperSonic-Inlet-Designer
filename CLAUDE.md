# Working rules for this project

- Claude Code may implement physics modules, following `isentropic.py`'s style (numpy, a `_validate` helper, `ValueError` on bad input, scalar + array support, short formula docstrings).
- Never invent reference values. Every expected value in a test must either be a closed-form identity, a self-consistency check, or carry a `# SOURCE: NACA 1135 ...` comment (table/equation and page number) — and stay confirmed by the user before it's treated as ground truth.
- Work one module at a time: implement -> tests -> run full `pytest` -> stop and summarise. Don't start the next module until the user says "continue".
- One task per session. End each session with a green `pytest` run (skips are fine; failures and errors are not).
- Use plan mode for any change that touches more than 2 files.
- When tests pass, suggest a commit message — do not commit automatically.
