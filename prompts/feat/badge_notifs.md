# Goal: Bring iOS to Feature Parity with Android

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

## Objective

The feed has badge notifications that persist even after the user has clicked on the feed and seen the new feeditems. please fix this, the number just keeps growing
---

## Operational Rules

- **Use the Figma MCP tools** to fetch the design for the Map and Scan screens. Match the Figma layout exactly.
- **Use the existing TapOut theme** defined in `warnabrotha/warnabrotha/Theme/Win95Theme.swift` (renamed to TapOutTheme). Use `AppColors`, `.appFont()`, `.displayFont()`, `.cardStyle()`, `PrimaryButton`, `LiveBadge`, etc.
- **Follow the existing MVVM pattern.** All new state goes in `AppViewModel` as `@Published` properties. Do not create new ViewModel classes.
- **Follow the existing `APIClient` patterns.** It already has generic `get()`, `post()`, `delete()` helpers and a `buildRequest()` method. Use the same async/await pattern. The `getAllFeeds()` and `removeVote()` methods already exist.
- **Keep it native SwiftUI.** Use only Apple frameworks (MapKit, PhotosUI/UIImagePickerController, Foundation).
- **Do not modify `.xcodeproj` or `.pbxproj` files.** Flag any new files that need to be added to the Xcode target.
- Do not commit anything to git without prior permission.
- Ask questions if you are confused.
- I will build and run the app.

---