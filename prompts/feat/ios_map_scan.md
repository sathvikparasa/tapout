# Goal: Bring iOS to Feature Parity with Android

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

## Objective

The Android app has features that the iOS app is missing. Implement them on iOS to reach feature parity. Reference `diff.md` at the project root for the full gap list.

FIGMA FILE: https://www.figma.com/design/u4urUqE3Mns7qdHLs8LcE4/TapOut
LAYER TO REFERENCE: "CLAUDE IMPLEMENTATION" — specifically the **Campus Parking Map**, **Ticket Scanning Camera**, and **Confirm Ticket Data** frames.

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

## Key Files to Read First

| File | Purpose |
|------|---------|
| `warnabrotha/warnabrotha/Theme/Win95Theme.swift` | TapOut design system (colors, fonts, components) |
| `warnabrotha/warnabrotha/ContentView.swift` | Tab navigation — Map tab already stubbed |
| `warnabrotha/warnabrotha/Views/MapTab.swift` | Current "Coming Soon" stub — replace this |
| `warnabrotha/warnabrotha/ViewModels/AppViewModel.swift` | All state and business logic |
| `warnabrotha/warnabrotha/Services/APIClient.swift` | HTTP client — already has `getAllFeeds()`, `removeVote()`, `delete()` |
| `warnabrotha/warnabrotha/Models/APIModels.swift` | Data models — already has `AllFeedsResponse`, `VoteResult` |

Also reference the Android implementations for behavior details:

| Android File | What to Reference |
|------|---------|
| `android/.../ui/screens/MapTab.kt` | Map layout, bottom sheet, lot coordinates, actions |
| `android/.../ui/screens/ScanTab.kt` | Scan state machine, UI for each state |
| `android/.../data/model/ApiModels.kt` | `TicketScanResponse`, `GlobalStatsResponse` |
| `android/.../ui/viewmodel/AppViewModel.kt` | `ScanState` enum, scan methods, `checkInAtLot()`, `reportSightingAtLot()`, vote toggle logic |

---

## Feature 1: Full Map Implementation (MapTab)

Replace the "Coming Soon" stub in `Views/MapTab.swift` with a full interactive map.

**Use Apple MapKit** (not Google Maps). The Android version uses Google Maps — translate to the iOS equivalent.

### Requirements

- Full-screen `Map` view (SwiftUI MapKit, iOS 17+) centered on UC Davis campus: `38.5422, -121.7551`, zoom ~0.01 span
- Annotation markers for each parking lot using coordinates from `ParkingLot` model (the lots have `latitude`/`longitude` fields). Fall back to these hardcoded values if coordinates are nil:
  - MU: `38.544416, -121.749561`
  - HUTCH: `38.53969, -121.758182`
  - ARC: `38.54304, -121.757572`
- Green markers for selected lot, dimmer for unselected
- Floating search bar at the top for filtering lots by name or code
- Bottom sheet that appears when a lot is tapped, showing:
  - Lot name + code + `LiveBadge`
  - "Zone {id} • UC Davis Campus"
  - Stat cards: active parkers count, TAPS in last hour count
  - CHECK IN / CHECK OUT button (context-aware: shows "CHECK OUT" if user is parked at this lot, "CHECK IN" otherwise, disabled if parked elsewhere)
  - REPORT TAPS button (red)

### ViewModel Changes

Add these methods to `AppViewModel`:

- `checkInAtLot(_ lotId: Int)` — like `checkIn()` but takes a specific lot ID
- `reportSightingAtLot(_ lotId: Int, notes: String?)` — like `reportSighting()` but takes a specific lot ID
- `lotStats: [Int: ParkingLotWithStats]` — cached stats for all lots, populated by a new `refreshAllLotStats()` method that calls `getParkingLot(id:)` for each lot

---

## Feature 2: Ticket Scanning (ScanTab)

Create a new `Views/ScanTab.swift` and add it as a 4th tab in `ContentView.swift` (between Feed and Map).

### State Machine

Add to `AppViewModel`:

```
enum ScanState {
    case idle
    case preview
    case processing
    case success
    case error
}
```

Published properties:
- `scanState: ScanState = .idle`
- `scanImageData: Data? = nil`
- `scanResult: TicketScanResponse? = nil`
- `scanError: String? = nil`

Methods:
- `selectScanImage(_ data: Data)` — sets `scanImageData`, transitions to `.preview`
- `submitTicketScan()` — transitions to `.processing`, uploads image via `POST /ticket-scan` (multipart), transitions to `.success` or `.error`
- `resetScan()` — resets to `.idle`

### API Changes

Add to `APIClient`:

```swift
func scanTicket(imageData: Data) async throws -> TicketScanResponse
```

This should build a multipart/form-data request manually (not JSON). The form field name is `"image"`, filename `"ticket.jpg"`, content type `"image/jpeg"`. Use the existing `buildRequest()` helper for the URL and auth header, then set the body to multipart form data.

### Data Model

Add to `APIModels.swift`:

```swift
struct TicketScanResponse: Codable {
    let success: Bool
    let ticketDate: String?
    let ticketTime: String?
    let ticketLocation: String?
    let mappedLotId: Int?
    let mappedLotName: String?
    let mappedLotCode: String?
    let isRecent: Bool
    let sightingId: Int?
    let usersNotified: Int

    enum CodingKeys: String, CodingKey {
        case success
        case ticketDate = "ticket_date"
        case ticketTime = "ticket_time"
        case ticketLocation = "ticket_location"
        case mappedLotId = "mapped_lot_id"
        case mappedLotName = "mapped_lot_name"
        case mappedLotCode = "mapped_lot_code"
        case isRecent = "is_recent"
        case sightingId = "sighting_id"
        case usersNotified = "users_notified"
    }
}
```

### UI (each state)

- **IDLE:** Camera icon, "Scan a Ticket" title, description text, "Take Photo" button (opens camera), "Choose from Library" button (opens photo picker)
- **PREVIEW:** Image preview, "Submit Ticket" button, "Retake" button
- **PROCESSING:** Spinner, "Reading ticket..." title, "Extracting date, time, and location" subtitle
- **SUCCESS:** Success icon, "Ticket Details" card (date, time, location, mapped lot), result message (green if TAPS report created, gray if too old, red if location not recognized), "Scan Another" button
- **ERROR:** Error icon, "Could not read ticket" title, error message, "Try Again" button

Use `PHPickerViewController` (via UIViewControllerRepresentable) for gallery and `UIImagePickerController` with `.camera` source for camera.

### Tab Bar Update

In `ContentView.swift`, add the Scan tab as the 3rd tab (index 2), shifting Map to index 3. Use `"doc.viewfinder"` as the SF Symbol icon with label "Scan".

---

## Feature 3: Vote Toggle

The iOS `APIClient` already has `removeVote(sightingId:)`. Update `AppViewModel.vote()` to match Android behavior:

- If the user taps the **same vote type** they already have → call `removeVote()` (removes vote)
- If the user taps a **different vote type** → call `vote()` (changes vote)
- If the user has **no vote** → call `vote()` (creates vote)

---

## Feature 4: All-Lots Feed Aggregation

The iOS `APIClient` already has `getAllFeeds()` and `AllFeedsResponse` is already defined.

Update `AppViewModel`:
- Add `@Published var allFeedSightings: [FeedSighting] = []`
- Add a `loadAllFeeds()` method that calls `getAllFeeds()` and flattens all sightings into `allFeedSightings` sorted by `minutesAgo`
- Call `loadAllFeeds()` in `loadInitialData()`
- In `ProbabilityTab`, when "ALL LOTS" filter is selected, display `allFeedSightings` instead of `feed?.sightings`

---

## Feature 5: Global Statistics

Add to `APIModels.swift`:

```swift
struct GlobalStatsResponse: Codable {
    let totalRegisteredDevices: Int
    let totalParked: Int
    let totalSightingsToday: Int

    enum CodingKeys: String, CodingKey {
        case totalRegisteredDevices = "total_registered_devices"
        case totalParked = "total_parked"
        case totalSightingsToday = "total_sightings_today"
    }
}
```

Add to `APIClient`:

```swift
func getGlobalStats() async throws -> GlobalStatsResponse {
    return try await get(endpoint: "/stats")
}
```

Add to `AppViewModel`:
- `@Published var globalStats: GlobalStatsResponse? = nil`
- Fetch in `loadInitialData()`

Display the community stats somewhere visible (e.g., on the Dashboard below the risk meter, or in the Map tab). Match wherever the Figma places it.

---

## Files to Create

| File | Purpose |
|------|---------|
| `warnabrotha/warnabrotha/Views/ScanTab.swift` | Ticket scanning screen (all 5 states) |

## Files to Modify

| File | Changes |
|------|---------|
| `warnabrotha/warnabrotha/Views/MapTab.swift` | Replace stub with full MapKit implementation + bottom sheet |
| `warnabrotha/warnabrotha/ContentView.swift` | Add Scan tab (index 2), shift Map to index 3 |
| `warnabrotha/warnabrotha/ViewModels/AppViewModel.swift` | Add scan state/methods, `checkInAtLot()`, `reportSightingAtLot()`, `lotStats`, vote toggle, `allFeedSightings`, `globalStats` |
| `warnabrotha/warnabrotha/Services/APIClient.swift` | Add `scanTicket()`, `getGlobalStats()` |
| `warnabrotha/warnabrotha/Models/APIModels.swift` | Add `TicketScanResponse`, `GlobalStatsResponse` |
| `warnabrotha/warnabrotha/Views/ProbabilityTab.swift` | Use `allFeedSightings` when "ALL LOTS" is selected |

## Xcode Manual Steps

After implementation, the following files need to be added to the Xcode target manually:
- `Views/ScanTab.swift`

Add `NSCameraUsageDescription` to `Info.plist` with a message like "TapOut needs camera access to scan parking tickets."
