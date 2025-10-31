# AG-UI Parity Progress (Dojo Front-End)

_Updated: $(date '+%Y-%m-%d')_

## Summary

We have completed the first implementation slice for bringing Telegram Luka UX to the AG-UI Dojo client:

- Introduced a **UiContextProvider** with mocked `uiContext`/`taskList` payloads to simulate upcoming gateway events.
- Implemented navigation controls (mode ribbon, quick prompts, scope toggles) and embedded them into the Bot API chat panel.
- Added a locale selector with persisted state (localStorage + cookie) and header placement.
- Provided a command palette with `⌘/Ctrl + K` shortcut, laying groundwork for backend-driven commands.
- Ensured kiosk layout mirrors the planned two-column view with contextual panel and embedded iframe on the right.

## Completed Work

### State & Context
- `UiContextProvider` supplies mocked `uiContext` + `taskList`, exposes `sendCommand`/`sendQuickPrompt`, and will later connect to SSE/WebSocket streams.
- Added optimistic UI updates for mode selection and scope toggles.

### Navigation / Controls
- `ModeBar`, `QuickPromptStrip`, `ScopeControls` render server-driven UI, matching Telegram affordances.
- Command palette (`CommandPaletteTrigger`, `CommandPalette`) sits in the header with `⌘/Ctrl + K` support.

### Locale & Layout
- Locale management (`LocaleProvider`) persists user choice and sets the locale cookie for backend use.
- `LocaleSelector` displayed in viewer header.
- `BotApiChatPanel` now contains navigation controls and uses locale metadata when calling Copilot runtime.
- Layout simplified: `MainLayout` is just a flex container; contextual components render inside the chat panel.

### Health Check
- Added `/api/health_check` GET/HEAD endpoint for K8s probes.

## In Progress / Next Steps
- Replace mocked `uiContext`/`taskList` with real SSE/WebSocket events from gateway.
- Extend state to include task panel UI and form workflows.
- Map command palette entries to backend command data; support command results in UI.
- Build remaining contextual panels (profile, groups, catalog) per `uiContext.activeMode`.
- Annotate chat timeline with form steps, approvals, and event metadata.

## Key Files
- `src/contexts/ui-context.tsx`
- `src/components/navigation/{mode-bar, quick-prompt-strip, scope-controls, command-palette}.tsx`
- `src/components/bot-api-chat-panel.tsx`
- `src/components/layout/{main-layout, viewer-layout}.tsx`
- `src/contexts/locale-context.tsx`
- `src/mocks/ui-context.ts`
- `src/app/api/health_check/route.ts`

## Open Questions
- How should command metadata (icons, tooltips, deep links) be structured in backend payloads?
- Exact shape of `taskList` events (pagination, badges) once backend is wired.
- Localization pipeline for prompt/ribbon text—confirm reuse of `.po` strings vs. direct backend localization.
