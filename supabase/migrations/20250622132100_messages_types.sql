-- Migration: Remove sender_id and add sender ("manager" | "user") to messages table

ALTER TABLE messages
  DROP COLUMN IF EXISTS sender_id;

ALTER TABLE messages
  ADD COLUMN sender text CHECK (sender IN ('manager', 'user')) NOT NULL DEFAULT 'user';
