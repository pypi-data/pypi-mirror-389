-- Add parsing_config column to domain_configs table
-- This enables zero-deploy updates to LLM parsing prompts and rules

ALTER TABLE public.domain_configs
ADD COLUMN IF NOT EXISTS parsing_config JSONB;

-- Add comment explaining the structure
COMMENT ON COLUMN public.domain_configs.parsing_config IS 
'LLM-based parsing configuration including prompt templates, entity schemas, validation rules, and examples. 
Structure: {
  "system_prompt_template": "...",
  "entity_schema": {...},
  "parsing_rules": [...],
  "validation_rules": {...},
  "few_shot_examples": [...]
}';

-- Update audit trigger to track parsing_config changes
-- (Already handled by existing update_updated_at_column trigger)

