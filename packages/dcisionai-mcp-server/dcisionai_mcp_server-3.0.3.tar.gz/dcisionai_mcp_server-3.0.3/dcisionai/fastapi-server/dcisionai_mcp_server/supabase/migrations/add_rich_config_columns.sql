-- Add rich configuration columns to domain_configs table
-- These store domain-specific objectives, constraints, and sensitivity data

-- Add objective_config column for storing optimization objectives
ALTER TABLE domain_configs 
ADD COLUMN IF NOT EXISTS objective_config JSONB DEFAULT '{}'::jsonb;

-- Add constraints_config column for storing constraint definitions
ALTER TABLE domain_configs 
ADD COLUMN IF NOT EXISTS constraints_config JSONB DEFAULT '{}'::jsonb;

-- Add comments for documentation
COMMENT ON COLUMN domain_configs.objective_config IS 
'Stores optimization objectives, formulation, and weights. Structure: {
  "objectives": ["list of objectives"],
  "formulation": "mathematical formulation string"
}';

COMMENT ON COLUMN domain_configs.constraints_config IS 
'Stores constraint definitions and sensitivity data. Structure: {
  "constraints": ["human-readable constraints"],
  "constraint_formulas": ["mathematical constraint formulas"],
  "sensitive_constraints": [{"name": "...", "impact": "HIGH|MEDIUM|LOW", "detail": "..."}]
}';

-- Create index for faster queries on JSONB columns
CREATE INDEX IF NOT EXISTS idx_domain_configs_objective_config 
ON domain_configs USING GIN (objective_config);

CREATE INDEX IF NOT EXISTS idx_domain_configs_constraints_config 
ON domain_configs USING GIN (constraints_config);

