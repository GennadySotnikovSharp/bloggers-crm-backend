-- Add parser_thread_id to chats to allow parallel assistant threads
ALTER TABLE public.chats
ADD COLUMN parser_thread_id text NOT NULL;
