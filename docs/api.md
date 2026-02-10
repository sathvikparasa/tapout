# API Overview

The server requires endpoints for each of the following functionalities: 
- authentication (GET users, get device, delete, and update)
- GET recent sightings (filters by last 3 hours)
- POST a sighting (posts a report sighting and updates database)
- GET parking lots list
- GET Parking lot details
- GET parking sessions
- POST a parking session
- Notifications
- GET feed details (include details and specific )

## Rules
Make sure each endpoint is authenticated with a JWT Token, except the login/signup ones. The authentication can be based on a custom JWT or a Supabase issued JWT, preferred Supabase.

DO NOT COMMIT ANYTHING TO GIT WITHOUT MY KNOWLEDGE.

DO NOT REMOVE ANY FILES WITHOUT MY KNOWLEDGE/