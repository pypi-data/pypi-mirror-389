-- Migration: Add result_formatter_config column to domain_configs table
-- Purpose: Enable universal config-driven result formatting (Phase 2)
-- Date: 2024-10-31

-- Add the new column as JSONB (nullable for backwards compatibility)
ALTER TABLE domain_configs 
ADD COLUMN IF NOT EXISTS result_formatter_config JSONB;

-- Add a comment to document the column
COMMENT ON COLUMN domain_configs.result_formatter_config IS 
'Config-driven result formatter schema. Includes: entity_keys, data_provenance templates, structured_results templates. Enables adding new domains without code changes.';

-- Example structure (for documentation):
-- {
--   "entity_keys": [
--     {"key": "products", "display_name": "Products"},
--     {"key": "shelves", "display_name": "Shelves"}
--   ],
--   "solution_metric_paths": {
--     "assignment_count": "assignments.length"
--   },
--   "data_provenance": {
--     "problem_type": "Store Layout Optimization",
--     "data_provided_template": "{products} products and {shelves} shelves extracted"
--   },
--   "structured_results": {
--     "a_model_development": {
--       "title": "Model Development",
--       "description": "Description with {template_vars}"
--     },
--     ... (sections b-g)
--   }
-- }

