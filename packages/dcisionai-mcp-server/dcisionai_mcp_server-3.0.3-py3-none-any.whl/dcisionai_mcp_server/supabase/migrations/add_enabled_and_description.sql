-- Add enabled and description columns to domain_configs table
ALTER TABLE public.domain_configs
ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS description TEXT;

-- Update existing rows to set enabled=true
UPDATE public.domain_configs
SET enabled = true
WHERE enabled IS NULL;

