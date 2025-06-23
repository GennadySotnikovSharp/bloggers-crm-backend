-- ⚠️ Supabase AI prompt (for migration)
-- Generate the first SQL migration for a creator-marketing platform.
-- We already use Supabase Auth. DO NOT recreate auth.users.
-- All schema lives in "public". Role is stored in auth.users.role (varchar).
-- Use Postgres 15 syntax. Enable RLS. Add auditing.

-- ───────────────
-- ✅ EXTENSIONS
-- ───────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ───────────────
-- ✅ TABLE: chats
-- ───────────────
CREATE TABLE public.chats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  openai_thread_id text NOT NULL,
  marketer_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  blogger_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now()
);

-- ───────────────
-- ✅ TABLE: messages
-- ───────────────
CREATE TABLE public.messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id uuid REFERENCES public.chats(id) ON DELETE CASCADE,
  openai_message_id text,
  sender_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  content text NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- ───────────────
-- ✅ TABLE: deals
-- ───────────────
CREATE TABLE public.deals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id uuid UNIQUE REFERENCES public.chats(id) ON DELETE CASCADE,
  price_usd numeric(12, 2),
  availability text,
  discounts text,
  status text DEFAULT 'negotiating',
  updated_at timestamptz DEFAULT now()
);

-- ───────────────
-- ✅ TABLE: audit_log
-- ───────────────
CREATE TABLE public.audit_log (
  id bigserial PRIMARY KEY,
  actor_id uuid,
  action text,
  object_type text,
  object_id uuid,
  payload jsonb,
  at_time timestamptz DEFAULT now()
);

-- ───────────────
-- ✅ RLS: enable and define policies
-- ───────────────
ALTER TABLE public.chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deals ENABLE ROW LEVEL SECURITY;

-- 👤 Policy: Chats — user is marketer or blogger
CREATE POLICY "user can read their chats"
  ON public.chats FOR SELECT
  USING (
    auth.uid() = marketer_id OR auth.uid() = blogger_id
  );

-- 👤 Policy: Messages — user can see and send in their chats
CREATE POLICY "can read messages"
  ON public.messages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.chats c
      WHERE c.id = chat_id AND (auth.uid() = c.marketer_id OR auth.uid() = c.blogger_id)
    )
  );

CREATE POLICY "can send message"
  ON public.messages FOR INSERT
  WITH CHECK (
    sender_id = auth.uid()
    AND EXISTS (
      SELECT 1 FROM public.chats c
      WHERE c.id = chat_id AND (auth.uid() = c.marketer_id OR auth.uid() = c.blogger_id)
    )
  );

-- 👤 Policy: Deals — marketer can insert/update
CREATE POLICY "can view deals"
  ON public.deals FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.chats c
      WHERE c.id = chat_id AND (auth.uid() = c.marketer_id OR auth.uid() = c.blogger_id)
    )
  );

CREATE POLICY "marketer can update deals"
  ON public.deals FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.chats c
      JOIN auth.users u ON u.id = auth.uid()
      WHERE c.id = chat_id AND c.marketer_id = u.id AND u.role = 'marketing'
    )
  )
  WITH CHECK (true);

CREATE POLICY "marketer can insert deals"
  ON public.deals FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.chats c
      JOIN auth.users u ON u.id = auth.uid()
      WHERE c.id = chat_id AND c.marketer_id = u.id AND u.role = 'marketing'
    )
  );

-- ───────────────
-- ✅ TRIGGER: audit_log
-- ───────────────
CREATE OR REPLACE FUNCTION public.log_row_change()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.audit_log(actor_id, action, object_type, object_id, payload)
  VALUES (
    auth.uid(),
    TG_OP,
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id),
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD)::jsonb
         ELSE row_to_json(NEW)::jsonb END
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 🔁 Attach to tables
CREATE TRIGGER log_chats
AFTER INSERT OR UPDATE OR DELETE ON public.chats
FOR EACH ROW EXECUTE FUNCTION public.log_row_change();

CREATE TRIGGER log_messages
AFTER INSERT OR UPDATE OR DELETE ON public.messages
FOR EACH ROW EXECUTE FUNCTION public.log_row_change();

CREATE TRIGGER log_deals
AFTER INSERT OR UPDATE OR DELETE ON public.deals
FOR EACH ROW EXECUTE FUNCTION public.log_row_change();