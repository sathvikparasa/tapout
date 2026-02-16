# Goal

Migrate the existing DB to Cloud SQL in GCP.

# Here is an unpolished plan that Claude created before.

2. Create a database and user

gcloud sql databases create tapout --instance=warnabrotha-db
gcloud sql users set-password postgres --instance=warnabrotha-db --password=<new-password>

3. Update your connection strings

In backend/.env, swap the two DATABASE_URL values to point to Cloud SQL. From App Engine, you connect via the Unix
socket:

DATABASE_URL=postgresql+asyncpg://postgres:<password>@/<dbname>?host=/cloudsql/tapout-485821:us-west1:warnabrotha-db
DATABASE_URL_SYNC=postgresql://postgres:<password>@/<dbname>?host=/cloudsql/tapout-485821:us-west1:warnabrotha-db

4. Enable the Cloud SQL connection in App Engine

In your app.yaml (or create one), add:
beta_settings:
cloud_sql_instances: tapout-485821:us-west1:warnabrotha-db

5. Migrate existing data (if any)

Export from Supabase and import to Cloud SQL:

# Export from Supabase

pg_dump "postgresql://postgres:<password>@db.nwhqbrvarztzaggnnoot.supabase.co:5432/postgres" > dump.sql

# Import to Cloud SQL (via Cloud SQL Proxy or authorized network)

psql "postgresql://postgres:<password>@<cloud-sql-ip>/warnabrotha" < dump.sql

6. Deploy and verify

Your SQLAlchemy models, API code, and tests don't need any changes — they're database-agnostic through the ORM. The
only change is the connection string

Make sure you use the gcloud cli. there is also an existing gcloud Cloud SQL instance of a database called tapout, everythings called tapout.

Use that.
