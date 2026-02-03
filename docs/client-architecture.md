# WarnABrotha Client Architecture

## Overview

The iOS client follows the **MVVM (Model-View-ViewModel)** pattern built entirely with **SwiftUI** and **zero third-party dependencies**. All networking, storage, and UI use native Apple frameworks.

## Main Components

### 1. ContentView (Root Navigation)
`ContentView.swift` — The app's root view. Uses conditional rendering based on authentication state to display one of three flows:
- **WelcomeView** — Registration for unauthenticated users
- **EmailVerificationView** — UC Davis email verification
- **Main Tab UI** — Two-tab interface (Report + Feed)

### 2. ButtonsTab (Report Tab)
`Views/ButtonsTab.swift` — Primary action screen. Contains the parking lot dropdown selector, probability meter, and two main action buttons: "I SAW TAPS" (report a sighting) and "I PARKED HERE" / "I'M LEAVING" (check-in/check-out). Includes a status bar showing active parker count, recent reports, and parking status.

### 3. ProbabilityTab (Feed Tab)
`Views/ProbabilityTab.swift` — Displays a scrollable feed of recent TAPS sightings with upvote/downvote functionality. Includes a lot selector and a probability meter. Each feed item shows timestamp, notes, and net vote score.

### 4. AppViewModel (State Manager)
`ViewModels/AppViewModel.swift` — The single centralized ViewModel managing all app state. Annotated with `@MainActor` for thread safety. Exposes `@Published` properties for auth state, parking lots, sessions, feed data, predictions, and UI state. All business logic flows through this class.

### 5. APIClient (Networking)
`Services/APIClient.swift` — Singleton HTTP client wrapping `URLSession`. Provides typed async methods for every backend endpoint (auth, lots, sessions, sightings, feed, predictions, notifications). Uses generic `get<T>()` and `post<T, B>()` methods with automatic JSON encoding/decoding. Attaches Bearer tokens from Keychain to authenticated requests.

### 6. KeychainService (Secure Storage)
`Services/KeychainService.swift` — Singleton wrapper around the iOS Security framework. Stores the auth token and a persistent device UUID. Uses `kSecAttrAccessibleAfterFirstUnlock` for the accessibility level.

### 7. APIModels (Data Structures)
`Models/APIModels.swift` — All Codable data transfer objects. Maps snake_case JSON from the backend to camelCase Swift properties via `CodingKeys`.

## Key Data Structures

| Model | Purpose |
|---|---|
| `ParkingLot` | Basic lot info (id, name, code, coordinates) |
| `ParkingLotWithStats` | Lot with active parkers, recent sightings, TAPS probability |
| `ParkingSession` | Active parking session with check-in/out timestamps |
| `FeedSighting` | Sighting with upvotes, downvotes, net score, user's vote |
| `PredictionResponse` | TAPS probability with breakdown factors and confidence |
| `TokenResponse` | JWT access token from registration |
| `VoteType` | Enum: `.upvote` / `.downvote` |

## Main Interfaces

### View <-> ViewModel
Views hold an `@ObservedObject var viewModel: AppViewModel`. User actions call async methods on the ViewModel (e.g., `viewModel.checkIn()`), which update `@Published` properties, causing SwiftUI to re-render automatically.

### ViewModel <-> APIClient
The ViewModel calls typed async methods on `APIClient.shared` (e.g., `api.getParkingLots() -> [ParkingLot]`). All methods throw `APIClientError` on failure, which the ViewModel catches and surfaces via `@Published var error`.

### APIClient <-> KeychainService
`APIClient` reads the auth token from `KeychainService.shared` when building authenticated requests. On registration, it writes the new token back to the Keychain.

### Navigation Flow
```
App Launch -> ContentView
  |-- No token  -> WelcomeView -> register() -> EmailVerificationView -> verifyEmail()
  +-- Has token -> checkAuthAndLoad() -> Main Tab UI
                                           |-- Tab 0: ButtonsTab (Report)
                                           +-- Tab 1: ProbabilityTab (Feed)
```
