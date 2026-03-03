#!/bin/bash
echo "🎯 DAT301 Workshop - Workshop Environment Setup"

# Create workshop directory and clone repository
mkdir -p /workshop
cd /workshop
git clone ${GITHUB_REPO_URL} .
git checkout ${GITHUB_BRANCH} || git checkout main || echo "Using default branch"

# Download mahavat-agent.zip from S3 (only if variables are set)
if [ -n "${ASSETS_BUCKET_NAME}" ] && [ -n "${AWS_REGION}" ]; then
    echo "Downloading mahavat-agent.zip from workshop assets..."
    aws s3 cp "s3://${ASSETS_BUCKET_NAME}/${ASSETS_BUCKET_PREFIX}mahavat-agent.zip" /tmp/mahavat-agent.zip --region "${AWS_REGION}"
    if [ -f /tmp/mahavat-agent.zip ]; then
        echo "Extracting mahavat-agent.zip to /workshop/mahavat-agent/"
        mkdir -p /workshop/mahavat-agent
        cd /workshop/mahavat-agent
        unzip -q /tmp/mahavat-agent.zip
        echo "mahavat-agent.zip extracted successfully"
        cd /workshop
    else
        echo "Warning: mahavat-agent.zip not found in S3 bucket"
    fi
else
    echo "Skipping mahavat-agent download - S3 variables not set"
fi

# Get CloudFormation outputs - skip during bootstrap (dynamic script handles this later)
# The stack may still be CREATE_IN_PROGRESS at this point
echo "Skipping CloudFormation queries - will be configured by workshop-setup-complete-dynamic.sh"
DB_ENDPOINT=""
DB_SECRET_ARN=""
DB_CLUSTER_ARN=""
COGNITO_USER_POOL_ID=""
COGNITO_CLIENT_ID=""

# Create .env file
cat > /workshop/.env << EOF
AWS_REGION=${AWS_REGION}
AWS_DEFAULT_REGION=${AWS_REGION}
RDS_CLUSTER_ARN=$DB_CLUSTER_ARN
RDS_SECRET_ARN=$DB_SECRET_ARN
DATABASE_NAME=workshop_db
DATABASE_ENDPOINT=$DB_ENDPOINT
DATABASE_PORT=5432
DATABASE_SECRET_ARN=$DB_SECRET_ARN
HOST=$DB_ENDPOINT
COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID
COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID
EOF

# Disable git operations for security (DAT409 security pattern)
if [ -d "/workshop/.git" ]; then
    echo "🔒 Disabling git operations for security..."
    chmod -R 000 "/workshop/.git" 2>/dev/null || true
    rm -rf "/workshop/.git/hooks" 2>/dev/null || true
    echo "✅ Git operations disabled (participants cannot push changes)"
fi

# Set ownership
chown -R participant:participant /workshop/

echo "✅ Workshop environment setup completed"