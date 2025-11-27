# Agent Instructions

This repository does not currently enforce a formal style guide, but contributors should follow these guardrails:

- Use Python type hints and docstrings for all new functions and classes.
- Prefer small, composable modules with clear interfaces.
- Keep networked functionality deterministic by avoiding live calls in tests or examples.
- When adding ingestion flows, expose configuration via arguments or environment variables rather than hard-coding secrets.
- Provide concise documentation updates for any new tooling.
- Respect the user's request to append change notes to new `DIFF_*.md` files and recommendations to new `RECOMMENDATIONS_*.md` files rather than modifying existing ones.

These instructions apply to the entire repository.
