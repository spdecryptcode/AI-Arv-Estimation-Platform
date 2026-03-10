# Contributing

Guidelines for contributors to ensure consistency and quality.

## Code Style

- Python: Black + Flake8, adhere to PEP 8.
- JavaScript/TypeScript: ESLint with Airbnb rules, Prettier for formatting.
- Markdown: use [markdownlint](https://github.com/DavidAnson/markdownlint).

## Branching & Pull Requests

- Use feature branches named `feature/<short-description>` or
  `bugfix/<short-description>`.
- Open a PR against `main`; require at least one review.
- Include a description of the change and reference any relevant issue.
- Update documentation in `docs/` when adding or changing functionality.
- Run tests and ensure CI passes before merging.

## Testing

- Write unit tests for new backend endpoints and model components.
- Integration tests should exercise HTTP APIs; use the `tests/` folder.
- End-to-end tests (Playwright) for the frontend are encouraged.

## Commits

- Use conventional commits (e.g. `feat:`, `fix:`, `docs:`).
- Reference issue numbers when appropriate.

## Documentation

- Keep docs up-to-date; add a `Last updated:` line at the top of edited
  files.
- New features require accompanying documentation in the appropriate
  markdown file.

## Issues

- File bugs and feature requests in the repository issue tracker.
- Label issues accurately (`bug`, `enhancement`, `documentation`, etc.).

## Code Reviews

- Reviewers should check for logic, style, tests, and updated documentation.
- Approve when the PR meets quality standards; request changes otherwise.
