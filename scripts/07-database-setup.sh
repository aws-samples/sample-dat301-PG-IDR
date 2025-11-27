#!/bin/bash
echo "🗄️ DAT301 Workshop - Database Setup"

# Parse command-line arguments
# Usage: ./07-database-setup.sh <host> <port> <database> <username> <password> <region>
if [ $# -eq 6 ]; then
    # Arguments provided - use them
    MAIN_HOST="$1"
    MAIN_PORT="$2"
    MAIN_DB="$3"
    MAIN_USER="$4"
    MAIN_PASS="$5"
    AWS_REGION="$6"
    echo "📥 Using provided command-line arguments"
elif [ -n "$MAIN_SECRET_ARN" ]; then
    # Fallback to environment variables and secret fetch
    echo "📥 Fetching credentials from Secrets Manager"
    MAIN_SECRET=$(aws secretsmanager get-secret-value --secret-id "$MAIN_SECRET_ARN" --region ${AWS_REGION:-us-west-2} --query SecretString --output text)
    MAIN_HOST=$(echo $MAIN_SECRET | jq -r .host)
    MAIN_PORT=$(echo $MAIN_SECRET | jq -r .port)
    MAIN_USER=$(echo $MAIN_SECRET | jq -r .username)
    MAIN_PASS=$(echo $MAIN_SECRET | jq -r .password)
    MAIN_DB=$(echo $MAIN_SECRET | jq -r .dbname)
fi

# Check if main database connection variables are set
if [ -z "$MAIN_HOST" ] || [ -z "$MAIN_DB" ] || [ -z "$MAIN_USER" ] || [ -z "$MAIN_PASS" ]; then
    echo "❌ Error: Main database connection parameters not provided"
    echo ""
    echo "Usage: $0 <host> <port> <database> <username> <password> <region>"
    echo "   OR set MAIN_SECRET_ARN environment variable"
    echo ""
    echo "Example:"
    echo "  $0 mydb.cluster-xxx.us-west-2.rds.amazonaws.com 5432 workshop_db admin mypassword us-west-2"
    exit 1
fi

echo "📊 Connecting to: $MAIN_DB on $MAIN_HOST"

# Set PostgreSQL environment variables
export PGHOST=$MAIN_HOST
export PGPORT=${MAIN_PORT:-5432}
export PGDATABASE=$MAIN_DB
export PGUSER=$MAIN_USER
export PGPASSWORD=$MAIN_PASS

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_DIR="$SCRIPT_DIR/database"

# Check if SQL scripts directory exists
if [ ! -d "$SQL_DIR" ]; then
    echo "❌ Error: SQL scripts directory not found: $SQL_DIR"
    exit 1
fi

# Run SQL scripts in order
echo "📝 Executing database setup scripts..."
for script in "$SQL_DIR"/*.sql; do
    if [ -f "$script" ]; then
        echo "  → Running: $(basename $script)"
        psql -f "$script" 2>&1 | grep -v "already exists" | grep -v "NOTICE" || {
            echo "  ⚠️  Warning: $(basename $script) may have failed or already applied"
        }
    fi
done

# Unset password
unset PGPASSWORD

echo "✅ Database setup completed!"
