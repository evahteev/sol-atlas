BEGIN;

-- 1) Increase text size in the runtime table
ALTER TABLE public.act_ru_variable
  ALTER COLUMN text_ TYPE TEXT;

-- 2) Increase text size in the historic variable instance table
ALTER TABLE public.act_hi_varinst
  ALTER COLUMN text_ TYPE TEXT;

-- 3) Increase text size in the historic detail table
ALTER TABLE public.act_hi_detail
  ALTER COLUMN text_ TYPE TEXT;

-- 4) Increase text size in the historic task instance table for descriptions as we use them for prompts
ALTER TABLE public.act_hi_taskinst
    ALTER COLUMN description_ TYPE TEXT;
ALTER TABLE public.act_ru_task
    ALTER COLUMN description_ TYPE TEXT;

COMMIT;
