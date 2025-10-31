# Repository Guidelines

## Project Structure & Module Organization
Turbo drives the pnpm workspace. Demos live in `apps/` (`apps/dojo` is the flagship Next.js app; `apps/client-cli-example` covers CLI flows). Reusable agents, middlewares, and SDKs sit in `integrations/*/typescript`, `middlewares/`, and `sdks/typescript/packages/`. Long-form docs live in `docs/`; experiments land in `feature/`. Keep assets next to their owners—`apps/dojo/public/` is the shared static bucket.

## Build, Test, and Development Commands
- `pnpm install` — hydrate dependencies (Node ≥18).
- `pnpm dev` — run `turbo run dev`; target the Dojo UI with `pnpm --filter demo-viewer dev`.
- `pnpm build` — execute the Turbo graph, emitting `.next/` or `dist/`.
- `pnpm lint`, `pnpm check-types` — run ESLint and TypeScript checks.
- `pnpm test` — trigger registered tests; Playwright runs via `pnpm --filter copilotkit-e2e test` inside `apps/dojo/e2e/`.

## Coding Style & Naming Conventions
TypeScript is standard; add explicit types on exports and async boundaries. Prettier (two-space indent, double quotes) plus Next-flavored ESLint enforce formatting—run `pnpm format` before submitting. House React components in `apps/dojo/src/components/**`, hooks in `apps/dojo/src/hooks/**`, and server utilities in `apps/dojo/src/server/**`. Favor kebab-case files, PascalCase components, and reserve `index.ts` barrels for genuine import ergonomics.

## Testing Guidelines
Keep unit and integration tests beside code as `*.test.ts` or `*.spec.ts`. Playwright e2e suites live in `apps/dojo/e2e/`; prep fixtures with `./scripts/prep-dojo-everything.js` beforehand. Generate artifacts via `pnpm --filter copilotkit-e2e report` and attach them when debugging failures. Flag skipped specs in PRs so reviewers see remaining gaps.

## Commit & Pull Request Guidelines
Commits use short, imperative subjects, often prefixed with an emoji or scope (e.g., `🔐 AddJWT Authentication for GURU Engine (#46)`). Keep subjects ≤72 characters and reference tickets with `(#id)` when relevant. PRs should outline problem, solution, linked issues, and proof (screenshots or logs) for UI or CLI updates. Confirm `pnpm lint`, `pnpm check-types`, and targeted tests, tag owners for affected packages, and list deferred follow-ups.

## Environment & Configuration Notes
Runtime settings load from `.env*`; never commit secrets. Update validation in `apps/dojo/src/env.ts` when adding new variables and document required keys in your PR. Store provider credentials in the secret manager and include masked examples in `docs/`.

## Documentation & Resources
Start with `apps/dojo/README.md` for local setup and demo context. Integration guides live with their code in `integrations/**/README.md`, while cross-cutting notes (e.g., `CLAUDE.md`, `COPILOTKIT_404_FIX.md`) sit in `docs/` and `apps/dojo/`. When you formalize a workflow, refresh the right README and reference it here if it becomes standard.
