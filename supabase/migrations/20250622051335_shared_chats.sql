-- Migration: make chats and deals shared for all marketers
-- Remove policies that depend on marketer_id
DROP POLICY IF EXISTS "user can read their chats" ON chats;
DROP POLICY IF EXISTS "can read messages" ON messages;
DROP POLICY IF EXISTS "can send message" ON messages;
DROP POLICY IF EXISTS "can view deals" ON deals;
DROP POLICY IF EXISTS "marketer can update deals" ON deals;
DROP POLICY IF EXISTS "marketer can insert deals" ON deals;

-- Now remove the column
ALTER TABLE chats DROP COLUMN IF EXISTS marketer_id;

-- 1. Remove marketer_id from chats
ALTER TABLE chats DROP COLUMN IF EXISTS marketer_id;

-- 2. Remove related foreign key if exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chats_marketer_id_fkey'
    ) THEN
        ALTER TABLE chats DROP CONSTRAINT chats_marketer_id_fkey;
    END IF;
END$$;
