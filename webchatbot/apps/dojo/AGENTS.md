# Repository Guidelines

This guide keeps AG-UI Dojo contributions consistent. Review it before cutting a branch or opening a pull request so UI polish, agent demos, and automation stay aligned.

## Project Structure & Module Organization
- `src/app` contains the Next.js App Router, layouts, and API handlers; keep route logic inside its segment folders.
- `src/demos`, `src/examples`, and `src/agents` define the showcased CopilotKit integrations—duplicate a nearby demo when adding a new one.
- Shared UI sits in `src/components`, while reusable helpers live in `src/lib`, `src/utils`, and React context under `src/contexts`.
- Static assets live in `public/`; `scripts/generate-content-json.ts` and `scripts/dev.mjs` assemble the demo catalog consumed at dev and production startup.
- Playwright fixtures, reporters, and helpers reside in `e2e/`; treat it as its own pnpm workspace when expanding coverage.

## Build, Test, and Development Commands
- `pnpm install` installs dependencies (requires the repo-level pnpm setup plus Homebrew `protobuf` as noted in `README.md`).
- `pnpm run dev` rebuilds the demo catalog then starts `next dev` on `http://localhost:3000`; add `NEXT_DEV_HTTPS=1` for Telegram Mini App testing.
- `pnpm run build` generates the optimized Next.js output; confirm production behavior with `pnpm start`, which reuses `generate-content-json`.
- `pnpm run lint` applies the Next.js + Tailwind ESLint config—run it before every push to keep CI clean.
- End-to-end checks: `pnpm --filter copilotkit-e2e test` (or `test:ui` for interactive debugging) exercises the Playwright suite.

## Coding Style & Naming Conventions
- Code in TypeScript + React with two-space indentation and modern functional components; reserve server components for data-bound routes.
- Name React components `PascalCase.tsx`, hooks and utilities `camelCase.ts`, and constants `SCREAMING_SNAKE_CASE`.
- Tailwind utility classes are the default styling approach; reach for component-scoped CSS only when composition becomes unwieldy.
- ESLint and formatting run via `pnpm run lint`; avoid inline `eslint-disable` blocks and document any rule exceptions in the PR description.

## Testing Guidelines
- Co-locate unit tests as `.test.ts` or `.test.tsx` beside the feature under test to mirror the import graph.
- Keep Playwright specs in `e2e/tests` with the `*.spec.ts` suffix and reuse helpers from `e2e/lib` so selectors remain stable.
- Capture failure artifacts (screenshots, traces) during Playwright runs and attach them to PR discussions when regressions appear.
- Update fixtures or demo metadata whenever `scripts/generate-content-json.ts` changes to keep navigation and catalog tests green.

## Commit & Pull Request Guidelines
- Commits stay short, imperative, and under ~72 characters (see `git log`: `fix the docker build`); expand on context in the body if needed.
- PR descriptions should summarize the scenario, list manual validation (`pnpm run lint`, Playwright command, etc.), and link issues or specs.
- Include screenshots or GIFs for UI-facing changes and call out API or schema updates that impact downstream demos.
- Request a second reviewer when touching shared contexts, SSE routes, or agent-protocol logic that other teams consume.
