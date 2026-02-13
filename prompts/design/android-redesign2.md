# Claude Code Prompt — Full UI Redesign

Paste this into Claude Code from your project root:

---

I'm replacing the entire UI of my Android app with a new design from Figma. Before writing any code, I need you to do a thorough investigation of the current codebase and then implement the new design.

## Figma Design

https://www.figma.com/design/u4urUqE3Mns7qdHLs8LcE4/TapOut?node-id=0-1&p=f&t=Qfskerx3ciZ1Wmnm-0

Use the Figma MCP to pull the full design — every screen, component, color, font, spacing value, and asset.

## Phase 1: Codebase Audit (do this BEFORE writing any code)

1. **Map the full project structure** — understand how files and packages are organized.
2. **Inventory all existing screens/composables** — list every screen, what it does, and what navigation routes connect them.
3. **Trace all API integrations** — find every API endpoint, network call, and repository. Document which screens use which endpoints and what data flows where.
4. **Identify state management patterns** — how is state handled (ViewModels, StateFlow, etc.)? What dependencies exist between screens?
5. **Catalog all business logic** — authentication flows, validation, data transformations, local storage, etc.
6. **Note any third-party SDKs/libraries** in use (Retrofit, Hilt, Room, etc.).

Present me with a summary of your findings before moving on.

## Phase 2: Design Mapping

After I approve the audit:

1. **Map each Figma screen to its existing counterpart** in the codebase (or flag new screens that don't have one yet).
2. **Identify which existing functionality/API hooks belong to which elements** in the new design (e.g., "this button in the new design maps to the existing `submitOrder()` call").
3. **Flag any screens or interactions in the new design that have NO existing backend support** so I know what's new.

Present this mapping for my review before proceeding.

## Phase 3: Implementation

After I approve the mapping:

1. **Replace the UI screen by screen** using Kotlin + Jetpack Compose.
2. **Preserve ALL existing functionality** — every API call, navigation flow, ViewModel, and piece of business logic must remain intact. The app should work exactly as it did before, just with the new UI.
3. **Follow existing code conventions** — match the current architecture, naming patterns, package structure, and dependency injection setup.
4. **Extract a clean design system** — create a theme/design tokens file from the Figma design (colors, typography, spacing) so the new UI is consistent and maintainable.
5. **Implement one screen at a time** and tell me what you've done after each so I can review incrementally.

## Features to Preserve That Are NOT in the Figma Design

Some existing features are missing from the new Figma design but must be kept:

1. **Search bar on the Campus Parking Map page** — The current implementation has a search bar that [describe what it searches — e.g., "lets users search for specific parking lots/buildings and the map pans to that location"]. This feature must be carried over into the new UI even though it doesn't appear in the Figma design. Integrate it in a way that fits naturally with the new design language.

> **Add any other features here that exist in the current app but are missing from the Figma design.** Review each screen carefully before running this prompt.

## New Screens (No Existing Implementation)

The following screens in the Figma design are brand new and have no existing code:

### 1. Confirm Ticket Data Page
- [Describe what this page should do — e.g., "Displays scanned ticket info (event name, date, seat, ticket holder) and lets the user confirm or reject the ticket before entry."]
- [What API endpoint should it call, if any? Or is this just displaying data passed from the scanner?]
- [Any validation logic needed?]

### 2. Ticket Scanning Camera Page
- [What scanning method? e.g., "Use CameraX + ML Kit barcode scanning to read QR codes on tickets."]
- [What data is encoded in the QR/barcode? e.g., a ticket ID that gets sent to an API?]
- [What happens on successful scan vs. failed scan?]
- [Any permissions handling notes?]

> **Fill in the bracketed sections above with your specifics before running this prompt.** The more detail you give on these new screens, the less Claude Code has to guess.

## Rules

- Do NOT delete or break any existing API integrations, business logic, or data layer code.
- If something in the Figma design is ambiguous, ask me rather than guessing.
- If the new design requires new API endpoints or features that don't exist yet, stub them out and flag them clearly.
- Keep commits/changes granular — one screen or logical unit at a time.
