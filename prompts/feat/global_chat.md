# Feature: Global Chat (replaces Ticket Scanning)

> Follow all rules in `prompts/overview.md` first.

## What to Build

Replace the Ticket Scanning page with a Global Chat screen with two features:
1. **Anonymous chat** — messages are not tied to user identity; no names stored
2. **AI content moderation** — filter messages before display or storage

## Design Reference

Use the Figma MCP tools to fetch the design.

- **File:** `https://www.figma.com/design/u4urUqE3Mns7qdHLs8LcE4/TapOut`
- **Layer group:** `CLAUDE IMPLEMENTATION` → frames: **Campus Parking Map**, **Ticket Scanning Camera**, **Confirm Ticket Data**

Match the Figma layout exactly.

## iOS Implementation Rules

- **Theme:** Use `AppColors`, `.appFont()`, `.displayFont()`, `.cardStyle()`, `PrimaryButton`, `LiveBadge` from `warnabrotha/warnabrotha/Theme/Win95Theme.swift` (renamed TapOutTheme).
- **State:** Add `@Published` properties to the existing `AppViewModel`. No new ViewModel classes.
- **Networking:** Use the existing `APIClient` helpers (`get()`, `post()`, `delete()`, `buildRequest()`). Follow the same async/await pattern.
- **UI:** SwiftUI only. Apple frameworks only (no third-party dependencies).
- **Project file:** Do not touch `.xcodeproj` / `.pbxproj`. Flag any new files that need to be added to the Xcode target manually.
