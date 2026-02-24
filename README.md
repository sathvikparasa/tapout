# TapOut

A parking enforcement tracking app for UC Davis students. Get real-time alerts when TAPS is spotted at your parking structure, check probability predictions, and help the community by reporting sightings.

**Website**: [tapoutparking.info](https://tapoutparking.info)

![TapOut App](screen.png)

## Overview

TapOut helps UC Davis students avoid parking tickets by:

- **Real-time Alerts**: Get notified instantly when TAPS is spotted at your parking lot
- **Check In/Out**: Register when you park to receive location-specific notifications
- **Community Reports**: Report TAPS sightings to warn fellow parkers
- **Reliability Voting**: Upvote/downvote reports to help identify accurate sightings
- **AI Predictions**: View probability predictions based on time, day, historical data, and academic calendar
- **3-Hour Reminders**: Automatic reminder to check out if you forget

### How It Works

1. **Register** your device and verify your UC Davis email
2. **Check in** when you park at a structure (e.g., Hutchinson)
3. **Receive alerts** if someone spots TAPS at your lot
4. **Report sightings** when you see TAPS to help others
5. **Vote on reports** to indicate reliability (thumbs up/down)
6. **Check out** when you leave

---

## Backend

### Tech Stack

- **Framework**: Python FastAPI
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Authentication**: JWT tokens + UC Davis email verification
- **Notifications**: APNs push notifications + in-app polling fallback
- **Background Tasks**: APScheduler for checkout reminders
- **Containerization**: Docker & Docker Compose

### Project Structure

```
backend/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── auth.py          # Device registration, email verification
│   │   ├── parking_lots.py  # Lot listing and details
│   │   ├── parking_sessions.py  # Check in/out
│   │   ├── sightings.py     # Report TAPS sightings
│   │   ├── feed.py          # Recent sightings feed + voting
│   │   ├── notifications.py # In-app notification polling
│   │   └── predictions.py   # AI probability predictions
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic
│   │   ├── auth.py          # UC Davis email verification, JWT
│   │   ├── notification.py  # APNs + polling notifications
│   │   ├── prediction.py    # ML probability model
│   │   └── reminder.py      # 3-hour checkout reminders
│   ├── config.py            # Environment configuration
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI application entry
├── tests/                   # Comprehensive test suite (83 tests)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register device, get JWT token |
| `/api/v1/auth/verify-email` | POST | Verify UC Davis email |
| `/api/v1/lots` | GET | List all parking lots |
| `/api/v1/lots/{id}` | GET | Get lot details with stats |
| `/api/v1/sessions/checkin` | POST | Check in to a lot |
| `/api/v1/sessions/checkout` | POST | Check out from current lot |
| `/api/v1/sightings` | POST | Report TAPS sighting |
| `/api/v1/feed` | GET | Get recent sightings (3 hrs) with votes |
| `/api/v1/feed/{lot_id}` | GET | Get feed for specific lot |
| `/api/v1/feed/sightings/{id}/vote` | POST | Upvote/downvote a sighting |
| `/api/v1/predictions/{lot_id}` | GET | Get TAPS probability prediction |
| `/api/v1/notifications/unread` | GET | Poll for new notifications |

### Running the Backend

```bash
# With Docker (recommended)
cd backend
docker-compose up --build

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

```bash
# Local development
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Optional: APNs for push notifications
APNS_KEY_ID=
APNS_TEAM_ID=
APNS_KEY_PATH=
APNS_BUNDLE_ID=
```

---

## Frontend

### Tech Stack

- **Framework**: SwiftUI (iOS)
- **Design**: Retro/pixelated, gamified UI

### App Structure

The app has two main tabs:

#### Tab 1: Buttons
- **Red "I saw TAPS" button**: Report a sighting (with confirmation popup)
- **Green "I parked at ___" button**: Check in to receive notifications
  - Transforms to **Yellow "I am leaving ___"** after check-in
- 3-hour automatic reminder if you don't check out

#### Tab 2: Probability & Feed
- **Probability Display**:
  - Animated counter (0-100%)
  - Color-coded: 🟢 Green (<33%) | 🟡 Yellow (33-66%) | 🔴 Red (>66%)
- **Recent Feed**:
  - Sightings from last 3 hours
  - Ordered by timestamp (newest first)
  - Thumbs up/down voting for reliability
  - Shows upvote/downvote counts and net score

### Supported Parking Structures

Currently tracking:
- Hutchinson Parking Structure

*More locations coming soon!*

---

## Feedback

We'd love to hear from you! Whether you have bug reports, feature requests, or just want to say hi:

### Contact Us

- **Email**: warnabrotha@ucdavis.edu
- **Discord**: discord.gg/warnabrotha
- **GitHub Issues**: [github.com/warnabrotha/app/issues](https://github.com/warnabrotha/app/issues)

### Team

- Claude Code

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Made with ❤️ by UC Davis students, for UC Davis students.*
