#!/bin/bash
echo "🚀 DAT301 Workshop - Master Setup Script"

# Set error handling
set -e

# Export environment variables from CloudFormation parameters
export AWS_REGION="${AWS::Region}"
export AWS_ACCOUNT_ID="${AWS::AccountId}"
export GITHUB_REPO_URL="${GitHubRepoUrl}"
export GITHUB_BRANCH="${GitHubBranch}"
export ASSETS_BUCKET_NAME="${AssetsBucketName}"
export ASSETS_BUCKET_PREFIX="${AssetsBucketPrefix}"
export WORKSHOP_STACK_NAME="${WorkshopStackName}"
export CODE_EDITOR_PASSWORD="${CodeEditorPassword}"

# Get the repo base URL for scripts
REPO_BASE_URL="https://raw.githubusercontent.com/rameshv29/riv25-dat301/main/scripts"

# Function to download and execute script
run_script() {
    local script_name=$1
    echo "📥 Downloading and executing $script_name..."
    curl -fsSL "$REPO_BASE_URL/$script_name" | bash
    echo "✅ $script_name completed"
}

# Execute scripts in order
run_script "01-system-setup.sh"
run_script "02-python-postgresql.sh"
run_script "03-code-server.sh"
run_script "04-workshop-setup.sh"
run_script "05-python-deps.sh"
#run_script "06-env-config.sh"
#run_script "07-database-setup.sh"
run_script "08-finalize.sh"

echo "🎉 All setup scripts completed successfully!"