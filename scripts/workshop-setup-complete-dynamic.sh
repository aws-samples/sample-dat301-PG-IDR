#!/bin/bash
set -e

echo "🚀 DAT301 Workshop - Complete Setup (Dynamic)"
echo "=============================================="

# Use environment variables set by code editor template
STACK_NAME="${WORKSHOP_STACK_NAME}"
REGION="${AWS_REGION:-us-west-2}"

if [ -z "$STACK_NAME" ]; then
    echo "❌ WORKSHOP_STACK_NAME not set. Cannot proceed."
    exit 1
fi

echo "📋 Using Stack: $STACK_NAME"
echo "📋 Using Region: $REGION"

# Retry function with exponential backoff
retry_with_backoff() {
    local max_attempts=10
    local delay=2
    local attempt=1
    local command="$@"
    
    while [ $attempt -le $max_attempts ]; do
        echo "  Attempt $attempt/$max_attempts..."
        if eval "$command"; then
            echo "  ✅ Success on attempt $attempt"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "  ❌ Failed after $max_attempts attempts"
            return 1
        fi
        
        echo "  ⏳ Waiting ${delay}s before retry..."
        sleep $delay
        delay=$((delay * 2))
        attempt=$((attempt + 1))
    done
}

# Function to get CloudFormation stack output
get_stack_output() {
    local output_key="$1"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" \
        --output text 2>/dev/null || echo ""
}

echo "📥 Fetching stack outputs..."

# Get all required outputs from CloudFormation (no retry needed - these are fast)
MAIN_SECRET_ARN=$(get_stack_output "DatabaseSecretArn")
IDR_SECRET_ARN=$(get_stack_output "IDRSecretArn")
IOPS_SECRET_ARN=$(get_stack_output "IDRInstanceSecretArn")
MAIN_ENDPOINT=$(get_stack_output "DatabaseEndpoint")
IDR_CLUSTER_ENDPOINT=$(get_stack_output "IDRClusterEndpoint")
IDR_INSTANCE_ENDPOINT=$(get_stack_output "IDRInstanceEndpoint")
MAIN_KB_ID=$(get_stack_output "MainKnowledgeBaseId")
MAIN_KB_BUCKET=$(get_stack_output "MainKnowledgeBaseBucket")
IDR_KB_ID=$(get_stack_output "IDRKnowledgeBaseId")
DYNAMODB_TABLE=$(get_stack_output "IDRIncidentTable")
IDR_CLUSTER_ARN=$(get_stack_output "IDRClusterArn")
RDS_CLUSTER_ARN=$(get_stack_output "MainDBClusterArn")
COGNITO_USER_POOL_ID=$(get_stack_output "CognitoUserPoolId")
COGNITO_CLIENT_ID=$(get_stack_output "CognitoClientId")

# Validate required outputs
if [ -z "$MAIN_SECRET_ARN" ] || [ -z "$MAIN_ENDPOINT" ]; then
    echo "❌ Failed to get required stack outputs. Check stack name and outputs."
    echo "Stack: $STACK_NAME"
    echo "Main Secret ARN: $MAIN_SECRET_ARN"
    echo "Main Endpoint: $MAIN_ENDPOINT"
    exit 1
fi

echo "✅ Stack outputs fetched successfully"

# Get database credentials from secrets
echo "🔐 Fetching database credentials..."

# Get Main DB credentials with retry
if [ -n "$MAIN_SECRET_ARN" ] && [ "$MAIN_SECRET_ARN" != "" ]; then
    echo "Fetching main database credentials..."
    if retry_with_backoff "aws secretsmanager get-secret-value --secret-id '$MAIN_SECRET_ARN' --region $REGION --query SecretString --output text > /tmp/main_secret.json"; then
        MAIN_SECRET=$(cat /tmp/main_secret.json)
        MAIN_HOST=$(echo $MAIN_SECRET | jq -r .host)
        MAIN_PORT=$(echo $MAIN_SECRET | jq -r .port)
        MAIN_USER=$(echo $MAIN_SECRET | jq -r .username)
        MAIN_PASS=$(echo $MAIN_SECRET | jq -r .password)
        MAIN_DB=$(echo $MAIN_SECRET | jq -r .dbname)
        rm -f /tmp/main_secret.json
    else
        echo "❌ Failed to fetch main database credentials"
        exit 1
    fi
else
    echo "⚠️  Main secret ARN not available"
fi

# Get IDR ACU DB credentials with retry
if [ -n "$IDR_SECRET_ARN" ] && [ "$IDR_SECRET_ARN" != "" ]; then
    echo "Fetching IDR ACU database credentials..."
    if retry_with_backoff "aws secretsmanager get-secret-value --secret-id '$IDR_SECRET_ARN' --region $REGION --query SecretString --output text > /tmp/idr_secret.json"; then
        IDR_SECRET=$(cat /tmp/idr_secret.json)
        IDR_HOST=$(echo $IDR_SECRET | jq -r .host)
        IDR_PORT=$(echo $IDR_SECRET | jq -r .port)
        IDR_USER=$(echo $IDR_SECRET | jq -r .username)
        IDR_PASS=$(echo $IDR_SECRET | jq -r .password)
        IDR_DB=$(echo $IDR_SECRET | jq -r .dbname)
        rm -f /tmp/idr_secret.json
    fi
else
    echo "⚠️  IDR ACU secret ARN not available"
fi

# Get IOPS DB credentials with retry
if [ -n "$IOPS_SECRET_ARN" ] && [ "$IOPS_SECRET_ARN" != "" ]; then
    echo "Fetching IDR IOPS database credentials..."
    if retry_with_backoff "aws secretsmanager get-secret-value --secret-id '$IOPS_SECRET_ARN' --region $REGION --query SecretString --output text > /tmp/iops_secret.json"; then
        IOPS_SECRET=$(cat /tmp/iops_secret.json)
        IOPS_HOST=$(echo $IOPS_SECRET | jq -r .host)
        IOPS_PORT=$(echo $IOPS_SECRET | jq -r .port)
        IOPS_USER=$(echo $IOPS_SECRET | jq -r .username)
        IOPS_PASS=$(echo $IOPS_SECRET | jq -r .password)
        IOPS_DB=$(echo $IOPS_SECRET | jq -r .dbname)
        rm -f /tmp/iops_secret.json
    fi
else
    echo "⚠️  IDR IOPS secret ARN not available"
fi

echo "✅ Database credentials fetched"

# Create psql connection functions in bashrc
echo "📝 Creating psql connection functions..."
cat >> /home/ec2-user/.bashrc << BASHRC_EOF

# PostgreSQL Connection Functions (Dynamic)
function psql_main() {
  PGHOST='$MAIN_HOST'
  PGPORT='$MAIN_PORT'
  PGUSER='$MAIN_USER'
  PGPASSWORD='$MAIN_PASS'
  PGDATABASE='$MAIN_DB'
  psql "\$@"
}

function psql_idr_acu() {
  PGHOST='$IDR_HOST'
  PGPORT='$IDR_PORT'
  PGUSER='$IDR_USER'
  PGPASSWORD='$IDR_PASS'
  PGDATABASE='$IDR_DB'
  psql "\$@"
}

function psql_idr_iops() {
  PGHOST='$IOPS_HOST'
  PGPORT='$IOPS_PORT'
  PGUSER='$IOPS_USER'
  PGPASSWORD='$IOPS_PASS'
  PGDATABASE='$IOPS_DB'
  psql "\$@"
}
BASHRC_EOF

echo "✅ psql functions created"

# Create comprehensive bashrc with all environment variables
echo "🔧 Creating workshop environment variables..."
cat >> /home/ec2-user/.bashrc << BASHRC_ENV_EOF

# DAT301 Workshop Environment Variables (Dynamic)

# AWS Configuration
export AWS_REGION=$REGION
export AWS_DEFAULT_REGION=$REGION
export WORKSHOP_STACK_NAME=$STACK_NAME

# Main Database (Production)
export RDS_SECRET_ARN=$MAIN_SECRET_ARN
export RDS_CLUSTER_ARN=$RDS_CLUSTER_ARN
export DATABASE_NAME=$MAIN_DB
export DB_SECRET_ARN=$MAIN_SECRET_ARN
export DB_ENDPOINT=$MAIN_HOST
export DB_PORT=$MAIN_PORT
export DB_USER=$MAIN_USER
export DB_PASS=$MAIN_PASS
export DB_NAME=$MAIN_DB
export MAIN_SECRET_ARN=$MAIN_SECRET_ARN

# PostgreSQL defaults (main database)
export PGHOST=$MAIN_HOST
export PGPORT=$MAIN_PORT
export PGUSER=$MAIN_USER
export PGPASSWORD=$MAIN_PASS
export PGDATABASE=$MAIN_DB

# Legacy aliases
export DATABASE_ENDPOINT=$MAIN_HOST
export DATABASE_PORT=$MAIN_PORT
export DATABASE_SECRET_ARN=$MAIN_SECRET_ARN
export HOST=$MAIN_HOST

# IDR ACU Cluster
export IDR_CLUSTER_ARN=$IDR_CLUSTER_ARN
export IDR_SECRET_ARN=$IDR_SECRET_ARN
export IDR_DATABASE_NAME=$IDR_DB
export IDR_CLUSTER_ENDPOINT=$IDR_HOST

# IDR IOPS Instance
export IOPS_SECRET_ARN=$IOPS_SECRET_ARN
export IDR_IOPS_ENDPOINT=$IOPS_HOST

# Knowledge Bases
export MAIN_KB_ID=$MAIN_KB_ID
export MAIN_KB_BUCKET=$MAIN_KB_BUCKET
export IDR_KB_ID=$IDR_KB_ID

# DynamoDB
export DYNAMODB_TABLE=$DYNAMODB_TABLE
export INCIDENT_TABLE=$DYNAMODB_TABLE

# Cognito
export COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID
export COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID
export DEMO_USERNAME=demo
export DEMO_PASSWORD=WorkshopDemo2025!

# Load testing aliases (using beautified scripts)
alias iops-test='/workshop/load-test/iops-test.sh'
alias acu-test='/workshop/load-test/acu-test.sh'
alias main-test='/workshop/load-test/run_stress_test.sh -s \$MAIN_SECRET_ARN -w CPU'

# Simulation aliases
alias simulation-2='cd /workshop/database-workload && python3 simulation-2.py'
alias simulation-3='cd /workshop/database-workload && python3 simulation-3.py'

# Mahavat Agent aliases
alias start-mahavat-v1='cd /workshop/mahavat_agent && /workshop/mahavat_agent/mahavat_agent_v1.sh'
alias start-mahavat-v2='cd /workshop/mahavat_agent && /workshop/mahavat_agent/mahavat_agent_v2.sh'

# Auto-activate virtual environment
if [ -f /workshop/mahavat_agent/venv/bin/activate ]; then
    source /workshop/mahavat_agent/venv/bin/activate
fi

# Workshop helper
alias workshop-env='env | grep -E "(AWS_|RDS_|DATABASE_|IDR_|PGHOST|PGPORT|PGUSER|PGDATABASE|KB_ID|DYNAMODB)" | sort'

echo "DAT301 Workshop environment loaded! Use 'workshop-env' to see all variables."
BASHRC_ENV_EOF

echo "✅ Environment variables configured"

# Setup mahavat_agent venv
echo "🐍 Setting up Python virtual environment..."
cd /workshop/mahavat_agent

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate and install requirements
source venv/bin/activate

echo "📦 Installing Python dependencies..."
pip3 install -q -r requirements.txt
deactivate

echo "✅ Python dependencies installed"

# Setup pgbench on IDR IOPS instance (if available)
if [ -n "$IOPS_HOST" ] && [ -n "$IOPS_PASS" ]; then
    echo "🔧 Setting up pgbench on IDR IOPS instance..."
    export PGPASSWORD=$IOPS_PASS
    retry_with_backoff "pgbench -i -s 200 -h $IOPS_HOST -p $IOPS_PORT -U $IOPS_USER -d $IOPS_DB" || echo "⚠️  pgbench setup failed (may already exist)"
    unset PGPASSWORD
    echo "✅ pgbench setup completed"
else
    echo "⚠️  IOPS instance not available, skipping pgbench setup"
fi

# Run database setup scripts on main database
echo "🗄️ Running database setup scripts on main database..."
retry_with_backoff "bash /workshop/scripts/07-database-setup.sh '$MAIN_HOST' '$MAIN_PORT' '$MAIN_DB' '$MAIN_USER' '$MAIN_PASS' '$REGION'" || echo "⚠️  Database setup had warnings (may already be configured)"

# Run extensions on IDR ACU cluster
if [ -n "$IDR_HOST" ] && [ -n "$IDR_PASS" ]; then
    echo "🔌 Installing extensions on IDR ACU cluster..."
    export PGPASSWORD="$IDR_PASS"
    retry_with_backoff "psql -h '$IDR_HOST' -p '$IDR_PORT' -U '$IDR_USER' -d '$IDR_DB' -f /workshop/scripts/database/01-extensions.sql" || echo "⚠️  Extensions may already be installed on IDR ACU"
    unset PGPASSWORD
fi

# Run extensions on IDR IOPS instance (if available)
if [ -n "$IOPS_HOST" ] && [ "$IOPS_HOST" != "None" ]; then
    echo "🔌 Installing extensions on IDR IOPS instance..."
    export PGPASSWORD="$IOPS_PASS"
    retry_with_backoff "psql -h '$IOPS_HOST' -p '$IOPS_PORT' -U '$IOPS_USER' -d '$IOPS_DB' -f /workshop/scripts/database/01-extensions.sql" || echo "⚠️  Extensions may already be installed on IDR IOPS"
    unset PGPASSWORD
fi

# Enable Performance Insights on all database instances
echo "📊 Checking Performance Insights status..."

# Function to enable Performance Insights on an instance
enable_performance_insights() {
    local instance_id=$1
    local instance_name=$2
    
    echo "  Checking $instance_name ($instance_id)..."
    
    # Check if Performance Insights is enabled with retry
    if retry_with_backoff "aws rds describe-db-instances --db-instance-identifier '$instance_id' --region '$REGION' --query 'DBInstances[0].PerformanceInsightsEnabled' --output text > /tmp/pi_status.txt"; then
        pi_enabled=$(cat /tmp/pi_status.txt)
        rm -f /tmp/pi_status.txt
        
        if [ "$pi_enabled" = "True" ]; then
            echo "  ✅ Performance Insights already enabled on $instance_name"
        else
            echo "  🔧 Enabling Performance Insights on $instance_name..."
            retry_with_backoff "aws rds modify-db-instance --db-instance-identifier '$instance_id' --enable-performance-insights --performance-insights-retention-period 7 --apply-immediately --region '$REGION'" >/dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                echo "  ✅ Performance Insights enabled on $instance_name"
            else
                echo "  ⚠️  Failed to enable Performance Insights on $instance_name"
            fi
        fi
    else
        echo "  ⚠️  Failed to check Performance Insights status on $instance_name"
    fi
}

# Get instance identifiers from cluster members
MAIN_INSTANCE=$(aws rds describe-db-clusters \
    --db-cluster-identifier "$(echo $MAIN_HOST | cut -d'.' -f1)" \
    --region "$REGION" \
    --query 'DBClusters[0].DBClusterMembers[0].DBInstanceIdentifier' \
    --output text 2>/dev/null)

IDR_ACU_INSTANCE=$(aws rds describe-db-clusters \
    --db-cluster-identifier "$(echo $IDR_HOST | cut -d'.' -f1)" \
    --region "$REGION" \
    --query 'DBClusters[0].DBClusterMembers[0].DBInstanceIdentifier' \
    --output text 2>/dev/null)

# Enable Performance Insights on all instances
if [ -n "$MAIN_INSTANCE" ] && [ "$MAIN_INSTANCE" != "None" ]; then
    enable_performance_insights "$MAIN_INSTANCE" "Main Database"
fi

if [ -n "$IDR_ACU_INSTANCE" ] && [ "$IDR_ACU_INSTANCE" != "None" ]; then
    enable_performance_insights "$IDR_ACU_INSTANCE" "IDR ACU Cluster"
fi

if [ -n "$IOPS_INSTANCE" ] && [ "$IOPS_INSTANCE" != "None" ]; then
    enable_performance_insights "$IOPS_INSTANCE" "IDR IOPS Instance"
fi

echo "✅ Performance Insights check completed"

# Create Cognito demo user
echo "👤 Creating Cognito demo user..."
aws cognito-idp admin-create-user \
  --user-pool-id "$COGNITO_USER_POOL_ID" \
  --username demo \
  --user-attributes Name=email,Value=demo@workshop.local Name=email_verified,Value=true \
  --temporary-password TempPass123! \
  --message-action SUPPRESS \
  --region "$REGION" 2>/dev/null || echo "⚠️  Demo user may already exist"

aws cognito-idp admin-set-user-password \
  --user-pool-id "$COGNITO_USER_POOL_ID" \
  --username demo \
  --password WorkshopDemo2025! \
  --permanent \
  --region "$REGION" 2>/dev/null || echo "⚠️  Password may already be set"

echo "✅ Cognito demo user configured"

# Set ownership
chown -R ec2-user:ec2-user /workshop
chown ec2-user:ec2-user /home/ec2-user/.bashrc

sleep 300

# Clean up bootstrap incidents from DynamoDB
echo "🧹 Truncating DynamoDB table: $DYNAMODB_TABLE in region: $REGION"

# Get all keys and delete one by one (simple approach)
aws dynamodb scan --table-name "$DYNAMODB_TABLE" --region "$REGION" \
  --query 'Items[].[pk.S, sk.S]' --output text | \
while IFS=$'\t' read -r pk sk; do
  if [ -n "$pk" ] && [ -n "$sk" ]; then
    echo "Deleting: $pk | $sk"
    aws dynamodb delete-item \
      --table-name "$DYNAMODB_TABLE" \
      --region "$REGION" \
      --key "{\"pk\":{\"S\":\"$pk\"},\"sk\":{\"S\":\"$sk\"}}"
  fi
done

echo "✅ Table truncated"

# Configure code-server settings for optimal workshop experience
echo "⚙️ Configuring code-server settings..."

# Create code-server settings directory
mkdir -p /home/ec2-user/.local/share/code-server/User

# Copy workshop-optimized settings
cat > /home/ec2-user/.local/share/code-server/User/settings.json << 'EOF'
{
  "workbench.startupEditor": "none",
  "terminal.integrated.enablePersistentSessions": false,
  "terminal.integrated.confirmOnExit": "never",
  "terminal.integrated.copyOnSelection": true,
  "terminal.integrated.rightClickBehavior": "paste",
  "security.workspace.trust.enabled": false,
  "files.autoSave": "afterDelay",
  "editor.fontSize": 16,
  "terminal.integrated.fontSize": 16,
  "chat.disableAIFeatures": true,
  "editor.fontLigatures": false,
  "terminal.integrated.fontWeight": "normal"
}
EOF

# Ensure proper ownership
chown -R ec2-user:ec2-user /home/ec2-user/.local/share/code-server

echo "✅ Code-server settings configured"

echo ""
echo "🎉 Workshop setup completed successfully!"
echo ""
echo "📋 Configuration Summary:"
echo "  Stack Name: $STACK_NAME"
echo "  Main DB: $MAIN_HOST"
echo "  IDR Cluster: $IDR_HOST"
echo "  IDR Instance: $IOPS_HOST"
echo "  Main KB ID: $MAIN_KB_ID"
echo "  IDR KB ID: $IDR_KB_ID"
echo "  DynamoDB Table: $DYNAMODB_TABLE"
echo ""
echo "Available commands:"
echo "  - psql_main       : Connect to main database"
echo "  - psql_idr_acu    : Connect to IDR ACU cluster"
echo "  - psql_idr_iops   : Connect to IDR IOPS instance"
echo "  - iops-test       : Run IOPS stress test"
echo "  - acu-test        : Run ACU stress test"
echo "  - workshop-env    : Show all environment variables"
echo ""
echo "To start IDR agent:"
echo "  cd /workshop/mahavat_agent && ./start_idr.sh"
echo ""
