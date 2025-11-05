-- Migration: Create domain_configs table for DcisionAI-Solver
-- Purpose: Store domain-specific configurations for Universal LMEA solver
-- Date: 2025-01-30

-- Create domain_configs table
CREATE TABLE IF NOT EXISTS domain_configs (
    -- Identity
    id TEXT PRIMARY KEY,                    -- e.g., 'retail_layout', 'vrp', 'workforce'
    name TEXT NOT NULL,                     -- e.g., 'Store Layout Optimization'
    domain TEXT NOT NULL,                   -- e.g., 'retail', 'logistics', 'workforce'
    problem_type TEXT NOT NULL,             -- e.g., 'store_layout', 'vehicle_routing'
    description TEXT,                       -- User-facing description
    
    -- Status
    is_active BOOLEAN DEFAULT true,        -- Can be disabled without deletion
    version INTEGER DEFAULT 1,              -- For config versioning
    
    -- Expert Personas (stored as JSONB)
    domain_expert JSONB NOT NULL,           -- Domain expert profile and knowledge
    math_expert JSONB NOT NULL,             -- Math expert profile and formulation
    
    -- Objective Function Configuration
    objective_config JSONB NOT NULL,        -- Weights, components, formulation
    
    -- Constraints Configuration
    constraint_config JSONB NOT NULL,       -- Hard constraints, soft constraints, penalties
    
    -- Genetic Algorithm Parameters
    ga_params JSONB NOT NULL,               -- Population size, generations, rates, etc.
    
    -- LLM Parsing Configuration
    parse_config JSONB NOT NULL,            -- Prompt templates, data schema, validation rules
    
    -- Result Formatting Configuration
    result_config JSONB NOT NULL,           -- Templates, metrics, narrative structure
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT,
    updated_by TEXT,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT valid_version CHECK (version > 0),
    CONSTRAINT valid_usage_count CHECK (usage_count >= 0)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_domain_configs_domain ON domain_configs(domain);
CREATE INDEX IF NOT EXISTS idx_domain_configs_active ON domain_configs(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_domain_configs_usage ON domain_configs(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_domain_configs_last_used ON domain_configs(last_used_at DESC) WHERE last_used_at IS NOT NULL;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_domain_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp updates
-- Note: Triggers cannot use CREATE OR REPLACE, so we use conditional creation
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'domain_configs_updated'
    ) THEN
        CREATE TRIGGER domain_configs_updated
            BEFORE UPDATE ON domain_configs
            FOR EACH ROW
            EXECUTE FUNCTION update_domain_config_timestamp();
    END IF;
END $$;

-- Create config history table for audit trail
CREATE TABLE IF NOT EXISTS domain_config_history (
    id SERIAL PRIMARY KEY,
    config_id TEXT NOT NULL REFERENCES domain_configs(id) ON DELETE CASCADE,
    changed_fields JSONB NOT NULL,          -- What changed
    old_values JSONB,                       -- Previous values
    new_values JSONB,                       -- New values
    change_type TEXT NOT NULL,              -- 'create', 'update', 'delete'
    changed_by TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_reason TEXT                      -- Optional reason for change
);

-- Index for history queries
CREATE INDEX IF NOT EXISTS idx_config_history_config_id ON domain_config_history(config_id);
CREATE INDEX IF NOT EXISTS idx_config_history_changed_at ON domain_config_history(changed_at DESC);

-- Create function to log config changes
CREATE OR REPLACE FUNCTION log_domain_config_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO domain_config_history (config_id, changed_fields, new_values, change_type, changed_by)
        VALUES (NEW.id, '{"all": true}'::jsonb, to_jsonb(NEW), 'create', NEW.created_by);
    ELSIF TG_OP = 'UPDATE' THEN
        -- Log only if substantive fields changed (not just updated_at, usage_count)
        IF OLD.domain_expert IS DISTINCT FROM NEW.domain_expert OR
           OLD.math_expert IS DISTINCT FROM NEW.math_expert OR
           OLD.objective_config IS DISTINCT FROM NEW.objective_config OR
           OLD.constraint_config IS DISTINCT FROM NEW.constraint_config OR
           OLD.ga_params IS DISTINCT FROM NEW.ga_params OR
           OLD.parse_config IS DISTINCT FROM NEW.parse_config OR
           OLD.result_config IS DISTINCT FROM NEW.result_config THEN
            
            INSERT INTO domain_config_history (config_id, changed_fields, old_values, new_values, change_type, changed_by)
            VALUES (NEW.id, '{}'::jsonb, to_jsonb(OLD), to_jsonb(NEW), 'update', NEW.updated_by);
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO domain_config_history (config_id, changed_fields, old_values, change_type, changed_by)
        VALUES (OLD.id, '{"all": true}'::jsonb, to_jsonb(OLD), 'delete', OLD.updated_by);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for change logging
-- Note: We use AFTER for INSERT/UPDATE, BEFORE for DELETE to avoid FK constraint issues
DO $$
BEGIN
    -- Trigger for INSERT and UPDATE
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'log_domain_config_changes_after_trigger'
    ) THEN
        CREATE TRIGGER log_domain_config_changes_after_trigger
            AFTER INSERT OR UPDATE ON domain_configs
            FOR EACH ROW
            EXECUTE FUNCTION log_domain_config_changes();
    END IF;
    
    -- Trigger for DELETE (BEFORE to log before row is deleted)
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'log_domain_config_changes_before_delete_trigger'
    ) THEN
        CREATE TRIGGER log_domain_config_changes_before_delete_trigger
            BEFORE DELETE ON domain_configs
            FOR EACH ROW
            EXECUTE FUNCTION log_domain_config_changes();
    END IF;
END $$;

-- Create view for active configs with usage stats
CREATE OR REPLACE VIEW active_domain_configs AS
SELECT 
    id,
    name,
    domain,
    problem_type,
    description,
    version,
    usage_count,
    last_used_at,
    created_at,
    updated_at
FROM domain_configs
WHERE is_active = true
ORDER BY usage_count DESC;

-- Comments for documentation
COMMENT ON TABLE domain_configs IS 'Stores domain-specific configurations for DcisionAI-Solver (Universal LMEA)';
COMMENT ON COLUMN domain_configs.id IS 'Unique identifier (e.g., retail_layout, vrp)';
COMMENT ON COLUMN domain_configs.domain_expert IS 'Domain expert persona profile and priorities (JSONB)';
COMMENT ON COLUMN domain_configs.math_expert IS 'Mathematical expert formulation and problem classification (JSONB)';
COMMENT ON COLUMN domain_configs.objective_config IS 'Multi-objective function weights and components (JSONB)';
COMMENT ON COLUMN domain_configs.constraint_config IS 'Hard and soft constraints with penalties (JSONB)';
COMMENT ON COLUMN domain_configs.ga_params IS 'Genetic algorithm parameters (JSONB)';
COMMENT ON COLUMN domain_configs.parse_config IS 'LLM parsing prompts and data schema (JSONB)';
COMMENT ON COLUMN domain_configs.result_config IS 'Result formatting templates and metrics (JSONB)';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE ON domain_configs TO authenticated;
-- GRANT SELECT ON active_domain_configs TO authenticated;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Domain configs table created successfully!';
    RAISE NOTICE 'Tables: domain_configs, domain_config_history';
    RAISE NOTICE 'Views: active_domain_configs';
    RAISE NOTICE 'Triggers: automatic timestamps, change logging';
END $$;

