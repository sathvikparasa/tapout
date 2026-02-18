# Goal: Redesign iOS App UI to Match Figma

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

## Objective

The iOS app currently uses a Windows 95 retro theme that needs to be replaced. Redesign the entire iOS SwiftUI app to match a provided Figma design file pixel-for-pixel.

FIGMA FILE: https://www.figma.com/design/u4urUqE3Mns7qdHLs8LcE4/TapOut
LAYER TO REFERENCE: ALL PAGES IN LAYER "CLAUDE IMPLEMENTATION"
---

## Operational Rules

- **Use the Figma MCP tools** (`get_figma_data`, `download_figma_images`) to fetch the design. Do not guess colors, fonts, spacing, or layouts — pull everything from Figma.
- **Use the `@frontend-design` plugin** for all UI changes you make.
- **Do not modify `AppViewModel.swift`, `APIModels.swift`, or any Service files** unless absolutely necessary for a UI state change (e.g., adding a new `@Published` property). Business logic and API integration must remain untouched.
- **Do not break any functionality.** Every feature (reporting, check-in/out, feed, voting, notifications, auth) must still work. Match all frontend code to backend functionality — do not skip anything.
- **Keep it native SwiftUI.** No external UI libraries. Use only Apple frameworks.
- **Do not modify `.xcodeproj` or `.pbxproj` files.** Flag any Xcode-level changes needed and I will do them manually.
- Do not commit anything to git without prior permission.
- Ask questions if you are confused about the Figma design or app behavior.
- I will build and run the app.

---

## Key Files

Read all of these before making any changes:

| File | Purpose |
|------|---------|
| `warnabrotha/warnabrotha/Theme/Win95Theme.swift` | Current theme system — replace this entirely |
| `warnabrotha/warnabrotha/Views/ButtonsTab.swift` | Main report/action screen |
| `warnabrotha/warnabrotha/Views/ProbabilityTab.swift` | Feed screen |
| `warnabrotha/warnabrotha/Views/EmailVerificationView.swift` | Onboarding/auth flow |
| `warnabrotha/warnabrotha/ContentView.swift` | Main container with tab navigation |
| `warnabrotha/warnabrotha/ViewModels/AppViewModel.swift` | All state and business logic |
| `warnabrotha/warnabrotha/Models/APIModels.swift` | Data models |

---

## Task

1. **Fetch the Figma design.** The user will provide the Figma file URL. Explore all frames and pages to understand the full design system — colors, typography, spacing, components, layouts, icons, and assets.

2. **Extract the design system** from Figma: color palette, typography (font families, sizes, weights), spacing/corner radius values, component styles (buttons, cards, inputs, badges, nav), and any icons or image assets. Download assets via `download_figma_images` into `Assets.xcassets/`.

3. **Replace the Win95 theme** with a new theme file that mirrors the Figma design system exactly. Replace `Win95Theme.swift` with a clean `Theme.swift` (or similar). Define all colors, fonts, spacing, and reusable component styles.

4. **Redesign all views** to match the Figma layouts. Match the exact layout, hierarchy, spacing, and visual style. If the Figma changes the navigation structure (tabs, screens), update `ContentView.swift` accordingly. Respect iOS conventions — safe areas, dynamic type, proper hit targets (44pt minimum).

5. **Preserve all existing functionality.** Every API call, user action, and state binding must still work after the redesign. The tiny things matter — notification badges, status indicators, loading states, error handling, etc.
