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

# Get CloudFormation outputs (only if variables are set)
if [ -n "${WORKSHOP_STACK_NAME}" ] && [ -n "${AWS_REGION}" ]; then
    echo "Getting database information from CloudFormation stacks..."
    DB_ENDPOINT=$(aws cloudformation describe-stacks --stack-name "${WORKSHOP_STACK_NAME}" --region "${AWS_REGION}" --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' --output text 2>/dev/null || echo "")
    DB_SECRET_ARN=$(aws cloudformation describe-stacks --stack-name "${WORKSHOP_STACK_NAME}" --region "${AWS_REGION}" --query 'Stacks[0].Outputs[?OutputKey==`DatabaseSecretArn`].OutputValue' --output text 2>/dev/null || echo "")
    DB_CLUSTER_ARN="arn:aws:rds:${AWS_REGION}:${AWS_ACCOUNT_ID}:cluster:$(echo $DB_ENDPOINT | cut -d'.' -f1)"
    COGNITO_USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name "${WORKSHOP_STACK_NAME}" --region "${AWS_REGION}" --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' --output text 2>/dev/null || echo "")
    COGNITO_CLIENT_ID=$(aws cloudformation describe-stacks --stack-name "${WORKSHOP_STACK_NAME}" --region "${AWS_REGION}" --query 'Stacks[0].Outputs[?OutputKey==`CognitoClientId`].OutputValue' --output text 2>/dev/null || echo "")
else
    echo "Skipping CloudFormation queries - stack variables not set"
    DB_ENDPOINT="localhost"
    DB_SECRET_ARN=""
    DB_CLUSTER_ARN=""
    COGNITO_USER_POOL_ID=""
    COGNITO_CLIENT_ID=""
fi

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

# Set ownership
chown -R ec2-user:ec2-user /workshop/

echo "✅ Workshop environment setup completed"