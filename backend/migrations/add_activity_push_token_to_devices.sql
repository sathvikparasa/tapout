-- Migration: add activity_push_token to devices
-- Run this against the Google Cloud SQL instance before deploying the backend changes.
--
-- Up
ALTER TABLE devices
    ADD COLUMN IF NOT EXISTS activity_push_token VARCHAR(255);

-- Down (if you need to revert)
-- ALTER TABLE devices DROP COLUMN IF EXISTS activity_push_token;
