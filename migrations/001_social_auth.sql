-- Migration: password-based signups -> social login (Google/Facebook) + guests
-- Additive only - no data is removed. Safe to run on a live database.
--
-- Run in Supabase SQL Editor or:
--   psql "$SUPABASE_DATABASE_URL" -f migrations/001_social_auth.sql

BEGIN;

-- Passwords are no longer collected; legacy rows keep their hashes.
ALTER TABLE signups ALTER COLUMN password_hash DROP NOT NULL;

-- Account-based signups: e-mail of the logged-in player (NULL for guests
-- and legacy password-era rows).
ALTER TABLE signups ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);

-- Guest signups: added by a logged-in user, who is the only one (besides
-- admins) allowed to remove them.
ALTER TABLE signups ADD COLUMN IF NOT EXISTS is_guest BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE signups ADD COLUMN IF NOT EXISTS added_by_email VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_signups_user_email ON signups(user_email);

-- One account signup per game (guests are exempt).
CREATE UNIQUE INDEX IF NOT EXISTS uniq_account_signup_per_game
    ON signups (game_id, user_email)
    WHERE is_guest = FALSE AND user_email IS NOT NULL;

COMMIT;
