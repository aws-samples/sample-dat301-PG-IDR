#!/bin/bash
echo "🔧 DAT301 Workshop - Environment Configuration from Main Stack"

# Set default region
AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="$AWS_REGION"

# Get main stack name from environment (passed from CloudFormation UserData)
MAIN_STACK_NAME="${WORKSHOP_STACK_NAME:-}"

if [ -z "$MAIN_STACK_NAME" ]; then
    echo "⚠️  WORKSHOP_STACK_NAME not set, trying to discover main stack..."
    # Get all stacks starting with dat301-reinvent-main, then filter out nested stacks
    MAIN_STACK_NAME=$(aws cloudformation list-stacks \
        --region "$AWS_REGION" \
        --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
        --query "StackSummaries[?starts_with(StackName, 'dat301-reinvent-main')].StackName" \
        --output text 2>/dev/null | tr '\t' '\n' | grep -E '^dat301-reinvent-main$' | head -1)
    
    # If exact match not found, try to find the shortest name (likely the root)
    if [ -z "$MAIN_STACK_NAME" ]; then
        MAIN_STACK_NAME=$(aws cloudformation list-stacks \
            --region "$AWS_REGION" \
            --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
            --query "StackSummaries[?starts_with(StackName, 'dat301-reinvent-main')].StackName" \
            --output text 2>/dev/null | tr '\t' '\n' | awk '{print length, $0}' | sort -n | head -1 | cut -d' ' -f2-)
    fi
fi

echo "🔍 Using main stack: ${MAIN_STACK_NAME:-'Not found'}"

# Function to get stack output from main stack
get_stack_output() {
    local output_key="$1"
    aws cloudformation describe-stacks \
        --stack-name "$MAIN_STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" \
        --output text 2>/dev/null || echo ""
}

# Get database outputs from MAIN stack (not nested DatabaseStack)
if [ -n "$MAIN_STACK_NAME" ]; then
    echo "📊 Extracting outputs from main stack..."
    
    # Database outputs
    DB_ENDPOINT=$(get_stack_output "DatabaseEndpoint")
    DB_SECRET_ARN=$(get_stack_output "DatabaseSecretArn")
    DB_CLUSTER_ID=$(get_stack_output "DBClusterIdentifier")
    DB_PORT=$(get_stack_output "DBPort")
    ENGINE_VERSION=$(get_stack_output "EngineVersion")
    
    # Construct cluster ARN if we have cluster ID
    if [ -n "$DB_CLUSTER_ID" ]; then
        DB_CLUSTER_ARN="arn:aws:rds:${AWS_REGION}:${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}:cluster:${DB_CLUSTER_ID}"
    else
        DB_CLUSTER_ARN=""
    fi
    
    # Cognito outputs
    COGNITO_USER_POOL_ID=$(get_stack_output "CognitoUserPoolId")
    COGNITO_CLIENT_ID=$(get_stack_output "CognitoClientId")
    COGNITO_IDENTITY_POOL_ID=$(get_stack_output "CognitoIdentityPoolId")
    ADMIN_USERNAME=$(get_stack_output "AdminUsername")
    READONLY_USERNAME=$(get_stack_output "ReadonlyUsername")
    DEFAULT_PASSWORD=$(get_stack_output "DefaultPassword")
else
    echo "⚠️  Main stack not found, using defaults"
    DB_ENDPOINT="localhost"
    DB_SECRET_ARN=""
    DB_CLUSTER_ARN=""
    DB_CLUSTER_ID=""
    DB_PORT="5432"
    ENGINE_VERSION=""
    COGNITO_USER_POOL_ID=""
    COGNITO_CLIENT_ID=""
    COGNITO_IDENTITY_POOL_ID=""
    ADMIN_USERNAME="admin"
    READONLY_USERNAME="readonly"
    DEFAULT_PASSWORD="TempPass123!"
fi

echo "✅ Stack outputs discovered:"
echo "   Main Stack: ${MAIN_STACK_NAME:-'Not found'}"
echo "   Database Endpoint: ${DB_ENDPOINT:-'Not found'}"
echo "   Database Secret: ${DB_SECRET_ARN:-'Not found'}"
echo "   Database Cluster: ${DB_CLUSTER_ID:-'Not found'}"
echo "   Cognito User Pool: ${COGNITO_USER_POOL_ID:-'Not found'}"
echo "   Cognito Client: ${COGNITO_CLIENT_ID:-'Not found'}"

# Create environment configuration
cat > /workshop/.env << EOF
# DAT301 Workshop Environment Variables (From Main Stack: ${MAIN_STACK_NAME})
AWS_REGION=$AWS_REGION
AWS_DEFAULT_REGION=$AWS_REGION

# Database Configuration (from main stack outputs)
DATABASE_ENDPOINT=${DB_ENDPOINT:-localhost}
DATABASE_PORT=${DB_PORT:-5432}
DATABASE_NAME=workshop_db
DB_CLUSTER_IDENTIFIER=${DB_CLUSTER_ID:-}
DB_CLUSTER_ARN=${DB_CLUSTER_ARN:-}
DB_SECRET_ARN=${DB_SECRET_ARN:-}
ENGINE_VERSION=${ENGINE_VERSION:-}

# Legacy aliases for compatibility
RDS_CLUSTER_ARN=${DB_CLUSTER_ARN:-}
RDS_SECRET_ARN=${DB_SECRET_ARN:-}
DATABASE_SECRET_ARN=${DB_SECRET_ARN:-}
HOST=${DB_ENDPOINT:-localhost}

# Cognito Configuration (from main stack outputs)
COGNITO_USER_POOL_ID=${COGNITO_USER_POOL_ID:-}
COGNITO_CLIENT_ID=${COGNITO_CLIENT_ID:-}
COGNITO_IDENTITY_POOL_ID=${COGNITO_IDENTITY_POOL_ID:-}
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
READONLY_USERNAME=${READONLY_USERNAME:-readonly}
DEFAULT_PASSWORD=${DEFAULT_PASSWORD:-TempPass123!}

# Stack Information
MAIN_STACK_NAME=${MAIN_STACK_NAME:-}
EOF

# Set up environment variables for ec2-user
cat >> /home/ec2-user/.bashrc << EOF

# DAT301 Workshop Environment Variables (From Main Stack: ${MAIN_STACK_NAME})
export AWS_REGION="$AWS_REGION"
export AWS_DEFAULT_REGION="$AWS_REGION"

# Database Configuration (from main stack outputs)
export DATABASE_ENDPOINT="${DB_ENDPOINT:-localhost}"
export DATABASE_PORT="${DB_PORT:-5432}"
export DATABASE_NAME=workshop_db
export DB_CLUSTER_IDENTIFIER="${DB_CLUSTER_ID:-}"
export DB_CLUSTER_ARN="${DB_CLUSTER_ARN:-}"
export DB_SECRET_ARN="${DB_SECRET_ARN:-}"

# Legacy aliases
export RDS_CLUSTER_ARN="${DB_CLUSTER_ARN:-}"
export RDS_SECRET_ARN="${DB_SECRET_ARN:-}"
export DATABASE_SECRET_ARN="${DB_SECRET_ARN:-}"
export HOST="${DB_ENDPOINT:-localhost}"

# Cognito Configuration (from main stack outputs)
export COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID:-}"
export COGNITO_CLIENT_ID="${COGNITO_CLIENT_ID:-}"
export COGNITO_IDENTITY_POOL_ID="${COGNITO_IDENTITY_POOL_ID:-}"
export ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
export READONLY_USERNAME="${READONLY_USERNAME:-readonly}"

# Workshop shortcuts
alias workshop-env='env | grep -E "(AWS_|RDS_|DATABASE_|HOST|COGNITO_|WORKSHOP_)" | sort'
alias workshop-info='echo "DAT301 Workshop Environment - Use workshop-env to see all variables"'
alias workshop-reload='source /workshop/.env && echo "Environment reloaded from /workshop/.env"'

# Auto-load workshop directory and environment
cd /workshop 2>/dev/null || true
if [ -f /workshop/.env ]; then
    set -a; source /workshop/.env; set +a
fi

echo "DAT301 Workshop environment loaded! Use 'workshop-env' to see all variables."
EOF

# Set ownership
chown ec2-user:ec2-user /workshop/.env

echo "✅ Environment configuration completed from main stack: ${MAIN_STACK_NAME}"
echo "📁 Environment file created: /workshop/.env"
echo "🔄 Run 'source ~/.bashrc' or start a new shell to load environment"