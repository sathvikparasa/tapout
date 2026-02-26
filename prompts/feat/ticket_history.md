# Goal: Revamp Scan Tab — Add Records/Scanner Toggle + Ticket History

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

---

## What to Build

Add a **Records | Scanner** pill switcher to the Scan tab header and implement a **Ticket History** list view. Design comes from two Figma frames already inspected (specs below — no need to re-fetch Figma):

- **"Scan Ticket-Ticket records"** (Figma node `337:178`) — the Records tab
- **"Confirm Ticket Data"** (Figma node `25:2`) — confirmation after scan (future scope, ignore for now)

---

## Files to Modify

| File | Change |
|------|--------|
| `warnabrotha/warnabrotha/ViewModels/AppViewModel.swift` | Add `ScanSubTab` enum + `scanSubTab` + `ticketHistory` + persistence helpers |
| `warnabrotha/warnabrotha/Models/APIModels.swift` | Add `TicketHistoryEntry` model |
| `warnabrotha/warnabrotha/Views/ScanTab.swift` | Full redesign — shared header, two sub-tabs |

Do **not** touch `.xcodeproj`, `.pbxproj`, backend, or any other file.

---

## Step 1 — New Model in `APIModels.swift`

Add under `// MARK: - Ticket Scanning`:

```swift
struct TicketHistoryEntry: Codable, Identifiable {
    let id: UUID
    let lotCode: String?      // e.g. "QUAD" — shown large in list
    let lotName: String?      // fallback display name
    let ticketDate: String?   // raw string from scan, e.g. "Oct 24, 2023"
    let ticketTime: String?   // raw string from scan, e.g. "10:24 AM"
    let ticketLocation: String?
    let scannedAt: Date       // when the user scanned it
    let sightingId: Int?
    let isRecent: Bool
}
```

---

## Step 2 — AppViewModel Changes

### 2a. New enum (add near `ScanState`):

```swift
enum ScanSubTab {
    case scanner
    case records
}
```

### 2b. New `@Published` properties (add in `// MARK: - Scan state`):

```swift
@Published var scanSubTab: ScanSubTab = .scanner
@Published var ticketHistory: [TicketHistoryEntry] = []
```

### 2c. Load history in `init()` after the existing guard block:

```swift
loadTicketHistory()
```

### 2d. New private helpers (add in `// MARK: - Scan Actions`):

```swift
func loadTicketHistory() {
    guard let data = UserDefaults.standard.data(forKey: "ticketHistory"),
          let entries = try? JSONDecoder().decode([TicketHistoryEntry].self, from: data) else { return }
    ticketHistory = entries
}

private func saveTicketToHistory(_ result: TicketScanResponse) {
    let entry = TicketHistoryEntry(
        id: UUID(),
        lotCode: result.mappedLotCode,
        lotName: result.mappedLotName,
        ticketDate: result.ticketDate,
        ticketTime: result.ticketTime,
        ticketLocation: result.ticketLocation,
        scannedAt: Date(),
        sightingId: result.sightingId,
        isRecent: result.isRecent
    )
    ticketHistory.insert(entry, at: 0)
    if ticketHistory.count > 50 { ticketHistory = Array(ticketHistory.prefix(50)) }
    if let data = try? JSONEncoder().encode(ticketHistory) {
        UserDefaults.standard.set(data, forKey: "ticketHistory")
    }
}
```

### 2e. In `submitTicketScan()`, after `scanState = .success`, add:

```swift
saveTicketToHistory(result)
```

---

## Step 3 — ScanTab.swift Full Redesign

Replace the entire file content. Structure:

```
ScanTab (VStack spacing:0, background: AppColors.background)
  ├── ScanHeader            ← always visible, contains pill switcher
  └── switch scanSubTab
        ├── .scanner → existing scan flow (no internal header)
        └── .records → TicketHistoryView
```

### 3a. `ScanHeader` design (from Figma node `337:302` + `337:338`)

```
VStack(spacing: 0), background rgba(247,247,247,0.8), ultraThinMaterial blur

  // Row 1: branding
  HStack {
    Text("TapOut")
      .displayFont(size: 17)          // DM Sans heavy
      .foregroundColor(AppColors.textPrimary)
    Spacer()
  }

  // Row 2: title + pill switcher
  HStack(alignment: .bottom) {
    Text("Scan Ticket")
      .displayFont(size: 30)
      .foregroundColor(AppColors.textPrimary)

    Spacer()

    // Pill switcher (HStack, no gap between pills — they share border)
    HStack(spacing: 0) {
      ScanPill(label: "Records",  isActive: scanSubTab == .records)  { scanSubTab = .records }
      ScanPill(label: "Scanner",  isActive: scanSubTab == .scanner)  { scanSubTab = .scanner }
    }
    .overlay(Capsule().stroke(AppColors.border, lineWidth: 1))
    .clipShape(Capsule())
  }

padding: .horizontal 24, .top 16, .bottom 24
```

`ScanPill` helper view:
```swift
// Active: AppColors.accent fill, white text
// Inactive: white fill, AppColors.textSecondary text
// Both: padding 10pt vertical, 20pt horizontal
// Shape: Capsule (borderRadius 9999)
```

### 3b. `TicketHistoryView` (Records tab, from Figma node `337:200`+children)

```
ScrollView {
  if ticketHistory.isEmpty {
    // Empty state — centered in remaining space
    VStack(spacing: 12) {
      Image(systemName: "doc.text.magnifyingglass")
        .font(.system(size: 40, weight: .light))
        .foregroundColor(AppColors.textMuted)
      Text("No tickets scanned yet")
        .appFont(size: 16, weight: .medium)
        .foregroundColor(AppColors.textSecondary)
      Text("Scan a parking ticket to see it here.")
        .appFont(size: 13)
        .foregroundColor(AppColors.textMuted)
        .multilineTextAlignment(.center)
    }
    .frame(maxWidth: .infinity, maxHeight: .infinity)
    .padding(.top, 80)
  } else {
    LazyVStack(spacing: 12) {
      ForEach(ticketHistory) { entry in
        TicketHistoryRow(entry: entry)
      }
    }
    .padding(.horizontal, 16)
    .padding(.top, 16)
    .padding(.bottom, 32)
  }
}
```

`TicketHistoryRow` — from Figma card style (node `337:200`):
```
HStack {
  // Left: lot code (large, bold)
  Text(entry.lotCode ?? entry.lotName ?? entry.ticketLocation ?? "Unknown")
    .appFont(size: 25, weight: .bold)        // Plus Jakarta Sans 25pt bold
    .foregroundColor(AppColors.textPrimary)
    .textCase(.uppercase)
    .lineLimit(1)

  Spacer()

  // Right: date + time stacked
  VStack(alignment: .trailing, spacing: 0) {
    Text(entry.ticketDate ?? formattedDate(entry.scannedAt))
      .displayFont(size: 14)                 // DM Sans 14pt extra-bold
      .foregroundColor(Color(hex: "141B34"))
    Text(entry.ticketTime ?? formattedTime(entry.scannedAt))
      .displayFont(size: 14)
      .foregroundColor(Color(hex: "141B34"))
  }
}
.padding(20)
.frame(maxWidth: .infinity, minHeight: 62)
.background(AppColors.cardBackground)
.clipShape(RoundedRectangle(cornerRadius: 12))
// Left green accent border (12pt) — use overlay trick:
.overlay(alignment: .leading) {
  Rectangle()
    .fill(AppColors.accent)
    .frame(width: 12)
    .clipShape(UnevenRoundedRectangle(
      topLeadingRadius: 12, bottomLeadingRadius: 12,
      bottomTrailingRadius: 0, topTrailingRadius: 0
    ))
}
.shadow(color: .black.opacity(0.05), radius: 2, y: 1)
.overlay(RoundedRectangle(cornerRadius: 12).stroke(AppColors.borderLight, lineWidth: 1))
```

Date/time fallback formatters (private helpers in the view):
```swift
private func formattedDate(_ date: Date) -> String {
    let f = DateFormatter(); f.dateStyle = .short; f.timeStyle = .none
    return f.string(from: date)
}
private func formattedTime(_ date: Date) -> String {
    let f = DateFormatter(); f.dateStyle = .none; f.timeStyle = .short
    return f.string(from: date)
}
```

### 3c. Scanner sub-tab

Reuse the existing `ScanIdleView`, `ScanPreviewView`, `ScanProcessingView`, `ScanSuccessView`, `ScanErrorView` **verbatim** — but strip their internal "Scan Ticket" header blocks (the shared `ScanHeader` replaces them). The state machine and logic stay identical.

---

## Constraints

- Use only `AppColors`, `.appFont()`, `.displayFont()`, `.cardStyle()`, `PrimaryButton`, `LiveBadge` from `AppTheme.swift`.
- All new state lives in `AppViewModel` as `@Published`. No new ViewModel classes.
- No new API calls. No backend changes.
- Do not modify `.xcodeproj` or `.pbxproj`. Flag any new Swift files that need to be added to the Xcode target.
- Do not commit to git.
- Ask questions if anything is unclear.
