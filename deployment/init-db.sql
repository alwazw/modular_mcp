-- Multi-Agent MCP System Database Initialization
-- This script sets up the initial database schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for different agents
CREATE SCHEMA IF NOT EXISTS agent1_scraper;
CREATE SCHEMA IF NOT EXISTS agent2_knowledge;
CREATE SCHEMA IF NOT EXISTS agent3_database;
CREATE SCHEMA IF NOT EXISTS agent4_transformer;
CREATE SCHEMA IF NOT EXISTS orchestrator;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA agent1_scraper TO mcp_user;
GRANT ALL PRIVILEGES ON SCHEMA agent2_knowledge TO mcp_user;
GRANT ALL PRIVILEGES ON SCHEMA agent3_database TO mcp_user;
GRANT ALL PRIVILEGES ON SCHEMA agent4_transformer TO mcp_user;
GRANT ALL PRIVILEGES ON SCHEMA orchestrator TO mcp_user;

-- Agent 1: Web Scraper Tables
CREATE TABLE IF NOT EXISTS agent1_scraper.scraping_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    result JSONB
);

CREATE TABLE IF NOT EXISTS agent1_scraper.file_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    upload_path TEXT,
    status VARCHAR(50) DEFAULT 'uploaded',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS agent1_scraper.browser_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name VARCHAR(255) NOT NULL,
    session_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Agent 2: Knowledge Base Tables
CREATE TABLE IF NOT EXISTS agent2_knowledge.knowledge_bases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSONB
);

CREATE TABLE IF NOT EXISTS agent2_knowledge.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_base_id UUID REFERENCES agent2_knowledge.knowledge_bases(id),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    file_path TEXT,
    document_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS agent2_knowledge.document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES agent2_knowledge.documents(id),
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    embedding VECTOR(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent 3: Database Manager Tables
CREATE TABLE IF NOT EXISTS agent3_database.database_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    connection_type VARCHAR(100),
    connection_string TEXT,
    encrypted_credentials TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS agent3_database.backup_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    database_id UUID REFERENCES agent3_database.database_connections(id),
    backup_type VARCHAR(100),
    backup_path TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    file_size BIGINT,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS agent3_database.analytics_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_name VARCHAR(255),
    sql_query TEXT,
    database_id UUID REFERENCES agent3_database.database_connections(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_executed TIMESTAMP,
    execution_count INTEGER DEFAULT 0
);

-- Agent 4: Data Transformer Tables
CREATE TABLE IF NOT EXISTS agent4_transformer.templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(100),  -- e.g., 'bestbuy', 'walmart'
    template_schema JSONB,
    field_definitions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS agent4_transformer.transformation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_template_id UUID REFERENCES agent4_transformer.templates(id),
    target_template_id UUID REFERENCES agent4_transformer.templates(id),
    input_data JSONB,
    output_data JSONB,
    transformation_rules JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent4_transformer.field_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_template_id UUID REFERENCES agent4_transformer.templates(id),
    target_template_id UUID REFERENCES agent4_transformer.templates(id),
    source_field VARCHAR(255),
    target_field VARCHAR(255),
    mapping_type VARCHAR(100),
    transformation_function TEXT,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT false
);

-- Orchestrator Tables
CREATE TABLE IF NOT EXISTS orchestrator.workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_definition JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS orchestrator.workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES orchestrator.workflows(id),
    status VARCHAR(50) DEFAULT 'running',
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS orchestrator.agent_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(255) NOT NULL,
    agent_url TEXT NOT NULL,
    agent_type VARCHAR(100),
    capabilities JSONB,
    health_status VARCHAR(50) DEFAULT 'unknown',
    last_health_check TIMESTAMP,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS orchestrator.webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_url TEXT NOT NULL,
    workflow_id UUID REFERENCES orchestrator.workflows(id),
    secret_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON agent1_scraper.scraping_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_created_at ON agent1_scraper.scraping_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_file_uploads_created_at ON agent1_scraper.file_uploads(created_at);

CREATE INDEX IF NOT EXISTS idx_documents_knowledge_base_id ON agent2_knowledge.documents(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON agent2_knowledge.documents(created_at);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON agent2_knowledge.document_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_backup_jobs_database_id ON agent3_database.backup_jobs(database_id);
CREATE INDEX IF NOT EXISTS idx_backup_jobs_created_at ON agent3_database.backup_jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_transformation_jobs_status ON agent4_transformer.transformation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_transformation_jobs_created_at ON agent4_transformer.transformation_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_field_mappings_templates ON agent4_transformer.field_mappings(source_template_id, target_template_id);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON orchestrator.workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON orchestrator.workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_registry_agent_name ON orchestrator.agent_registry(agent_name);

-- Insert initial data
INSERT INTO agent4_transformer.templates (name, platform, template_schema, field_definitions) VALUES
('BestBuy Product Template', 'bestbuy', 
 '{"fields": ["sku", "title", "description", "price", "category", "brand", "specifications"]}',
 '{"sku": {"type": "string", "required": true}, "title": {"type": "string", "required": true}, "price": {"type": "decimal", "required": true}}'),
('Walmart Product Template', 'walmart',
 '{"fields": ["item_id", "product_name", "product_description", "retail_price", "category_path", "manufacturer", "attributes"]}',
 '{"item_id": {"type": "string", "required": true}, "product_name": {"type": "string", "required": true}, "retail_price": {"type": "decimal", "required": true}}');

INSERT INTO agent2_knowledge.knowledge_bases (name, description) VALUES
('System Documentation', 'Documentation for the Multi-Agent MCP System'),
('Product Catalogs', 'Product information and catalogs'),
('User Manuals', 'User guides and manuals');

-- Create a function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_scraping_jobs_updated_at BEFORE UPDATE ON agent1_scraper.scraping_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_bases_updated_at BEFORE UPDATE ON agent2_knowledge.knowledge_bases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON agent2_knowledge.documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_database_connections_updated_at BEFORE UPDATE ON agent3_database.database_connections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON agent4_transformer.templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON orchestrator.workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant all necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agent1_scraper TO mcp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agent2_knowledge TO mcp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agent3_database TO mcp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agent4_transformer TO mcp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA orchestrator TO mcp_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agent1_scraper TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agent2_knowledge TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agent3_database TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agent4_transformer TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA orchestrator TO mcp_user;

