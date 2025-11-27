-- Create workshop admin role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'workshop_admin') THEN
        CREATE ROLE workshop_admin WITH LOGIN PASSWORD 'AdminPass2025!';
    END IF;
END
$$;

-- Grant admin privileges
GRANT ALL PRIVILEGES ON DATABASE workshop_db TO workshop_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO workshop_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO workshop_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO workshop_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO workshop_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO workshop_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO workshop_admin;

-- Create workshop readonly role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'workshop_readonly') THEN
        CREATE ROLE workshop_readonly WITH LOGIN PASSWORD 'ReadonlyPass2025!';
    END IF;
END
$$;

-- Grant readonly privileges
GRANT CONNECT ON DATABASE workshop_db TO workshop_readonly;
GRANT USAGE ON SCHEMA public TO workshop_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO workshop_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO workshop_readonly;
GRANT SELECT ON information_schema.tables TO workshop_readonly;
GRANT SELECT ON information_schema.columns TO workshop_readonly;
--GRANT SELECT ON pg_stat_user_tables TO workshop_readonly;
--GRANT SELECT ON pg_stat_user_indexes TO workshop_readonly;
--GRANT SELECT ON pg_stat_activity TO workshop_readonly;
--GRANT SELECT ON pg_stat_database TO workshop_readonly;
GRANT SELECT ON pg_stat_statements TO workshop_readonly;