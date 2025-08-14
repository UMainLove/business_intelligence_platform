-- PostgreSQL initialization script for Business Intelligence Platform
-- This script sets up the database schema and initial data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Business ventures table
CREATE TABLE IF NOT EXISTS business_ventures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    founded_date DATE,
    status VARCHAR(20) CHECK(status IN ('active', 'failed', 'acquired', 'ipo')),
    initial_funding DECIMAL(15,2),
    total_funding DECIMAL(15,2),
    valuation DECIMAL(15,2),
    employees INTEGER,
    revenue DECIMAL(15,2),
    region VARCHAR(100),
    business_model VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Industry benchmarks table
CREATE TABLE IF NOT EXISTS industry_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    industry VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(50),
    percentile INTEGER,
    year INTEGER,
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market events table
CREATE TABLE IF NOT EXISTS market_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_date DATE NOT NULL,
    event_type VARCHAR(100),
    industry VARCHAR(100),
    description TEXT,
    impact_level VARCHAR(20) CHECK(impact_level IN ('low', 'medium', 'high')),
    affected_companies JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial metrics table
CREATE TABLE IF NOT EXISTS financial_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    venture_id UUID REFERENCES business_ventures(id) ON DELETE CASCADE,
    metric_date DATE,
    revenue DECIMAL(15,2),
    profit_margin DECIMAL(5,2),
    customer_count INTEGER,
    cac DECIMAL(10,2),
    ltv DECIMAL(10,2),
    churn_rate DECIMAL(5,2),
    burn_rate DECIMAL(15,2),
    runway_months INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ventures_industry ON business_ventures(industry);
CREATE INDEX IF NOT EXISTS idx_ventures_status ON business_ventures(status);
CREATE INDEX IF NOT EXISTS idx_benchmarks_industry ON industry_benchmarks(industry);
CREATE INDEX IF NOT EXISTS idx_events_industry ON market_events(industry);
CREATE INDEX IF NOT EXISTS idx_metrics_venture ON financial_metrics(venture_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_business_ventures_updated_at
    BEFORE UPDATE ON business_ventures
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_industry_benchmarks_updated_at
    BEFORE UPDATE ON industry_benchmarks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_market_events_updated_at
    BEFORE UPDATE ON market_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_financial_metrics_updated_at
    BEFORE UPDATE ON financial_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (only if tables are empty)
INSERT INTO business_ventures (name, industry, founded_date, status, initial_funding, total_funding, valuation, employees, revenue, region, business_model)
SELECT * FROM (VALUES
    ('TechStart', 'SaaS', '2019-01-15', 'active', 1000000.00, 5000000.00, 25000000.00, 45, 3000000.00, 'North America', 'subscription'),
    ('EcommerceNow', 'E-commerce', '2018-03-20', 'acquired', 500000.00, 12000000.00, 80000000.00, 120, 15000000.00, 'Europe', 'marketplace'),
    ('FinTechInc', 'FinTech', '2020-06-10', 'active', 2000000.00, 15000000.00, 100000000.00, 80, 8000000.00, 'Asia', 'B2B'),
    ('FailedStartup', 'HealthTech', '2017-08-05', 'failed', 800000.00, 800000.00, 0.00, 0, 0.00, 'North America', 'B2C'),
    ('UnicornCorp', 'AI/ML', '2016-12-01', 'ipo', 5000000.00, 150000000.00, 2000000000.00, 500, 50000000.00, 'North America', 'enterprise')
) AS v(name, industry, founded_date, status, initial_funding, total_funding, valuation, employees, revenue, region, business_model)
WHERE NOT EXISTS (SELECT 1 FROM business_ventures LIMIT 1);

INSERT INTO industry_benchmarks (industry, metric_name, metric_value, metric_unit, percentile, year, source)
SELECT * FROM (VALUES
    ('SaaS', 'Customer Acquisition Cost', 120.00, 'USD', 50, 2024, 'Industry Report'),
    ('SaaS', 'Customer Lifetime Value', 480.00, 'USD', 50, 2024, 'Industry Report'),
    ('SaaS', 'Monthly Churn Rate', 5.20, 'percent', 50, 2024, 'Industry Report'),
    ('SaaS', 'Revenue Growth Rate', 25.00, 'percent', 75, 2024, 'Industry Report'),
    ('E-commerce', 'Conversion Rate', 2.80, 'percent', 50, 2024, 'E-commerce Study'),
    ('E-commerce', 'Average Order Value', 85.00, 'USD', 50, 2024, 'E-commerce Study'),
    ('FinTech', 'Customer Acquisition Cost', 180.00, 'USD', 50, 2024, 'FinTech Analysis')
) AS v(industry, metric_name, metric_value, metric_unit, percentile, year, source)
WHERE NOT EXISTS (SELECT 1 FROM industry_benchmarks LIMIT 1);