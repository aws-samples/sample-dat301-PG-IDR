#!/bin/bash
echo "🔍 DAT301 Workshop - Environment Validation"
echo "============================================"

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

echo ""
echo "1. System Python Check"
echo "----------------------"
SYSTEM_PYTHON=$(/usr/bin/python3 --version 2>&1)
if [[ $SYSTEM_PYTHON == *"3.9"* ]]; then
    check_pass "System Python intact: $SYSTEM_PYTHON"
else
    check_warn "System Python version unexpected: $SYSTEM_PYTHON (expected 3.9.x)"
fi

echo ""
echo "2. DNF/YUM Check"
echo "----------------"
if dnf --version &> /dev/null; then
    check_pass "DNF working correctly"
else
    check_fail "DNF not working - system Python may be broken"
fi

echo ""
echo "3. Pyenv Installation"
echo "---------------------"
if sudo -u ec2-user bash -c '[ -d "$HOME/.pyenv" ]'; then
    check_pass "Pyenv installed in user space"
    PYENV_PYTHON=$(sudo -u ec2-user bash -c 'export PYENV_ROOT="$HOME/.pyenv" && export PATH="$PYENV_ROOT/bin:$PATH" && eval "$(pyenv init -)" && cd /workshop && python --version 2>&1')
    if [[ $PYENV_PYTHON == *"3.11.13"* ]]; then
        check_pass "Workshop Python: $PYENV_PYTHON"
    else
        check_warn "Workshop Python version: $PYENV_PYTHON (expected 3.11.13)"
    fi
else
    check_fail "Pyenv not installed"
fi

echo ""
echo "4. UV Installation"
echo "------------------"
if sudo -u ec2-user bash -c '[ -f "$HOME/.local/bin/uv" ]'; then
    UV_VERSION=$(sudo -u ec2-user bash -c '$HOME/.local/bin/uv --version 2>&1')
    check_pass "UV installed: $UV_VERSION"
    
    if sudo -u ec2-user bash -c 'grep -q ".local/bin" ~/.bashrc'; then
        check_pass "UV in PATH (.bashrc)"
    else
        check_warn "UV not in PATH - may not be accessible in all contexts"
    fi
else
    check_fail "UV not installed"
fi

echo ""
echo "5. PostgreSQL Installation"
echo "--------------------------"
if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version)
    check_pass "PostgreSQL installed: $PG_VERSION"
else
    check_fail "PostgreSQL not installed"
fi

if rpm -q postgresql17-server-devel &> /dev/null; then
    check_pass "PostgreSQL development tools installed"
else
    check_warn "PostgreSQL development tools not fully installed"
fi

echo ""
echo "6. Code Server Installation"
echo "---------------------------"
if [ -f /usr/bin/code-server ]; then
    CODE_VERSION=$(code-server --version 2>&1 | head -1)
    check_pass "Code Server installed: $CODE_VERSION"
else
    check_fail "Code Server not installed"
fi

if [ -f /etc/systemd/system/code-server.service ]; then
    check_pass "Code Server systemd service configured"
    
    if systemctl is-active --quiet code-server; then
        check_pass "Code Server service running"
    else
        check_warn "Code Server service not running"
    fi
else
    check_fail "Code Server systemd service not configured"
fi

echo ""
echo "7. Workshop Directory"
echo "---------------------"
if [ -d /workshop ]; then
    check_pass "Workshop directory exists"
    
    if [ -f /workshop/.python-version ]; then
        PYENV_LOCAL=$(cat /workshop/.python-version)
        if [[ $PYENV_LOCAL == "3.11.13" ]]; then
            check_pass "Pyenv local version set: $PYENV_LOCAL"
        else
            check_warn "Pyenv local version: $PYENV_LOCAL (expected 3.11.13)"
        fi
    else
        check_warn "Pyenv local version not set in /workshop"
    fi
    
    if [ -d /workshop/.venv ]; then
        check_pass "Virtual environment exists"
    else
        check_warn "Virtual environment not created"
    fi
else
    check_fail "Workshop directory does not exist"
fi

echo ""
echo "8. AWS CLI"
echo "----------"
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1)
    check_pass "AWS CLI installed: $AWS_VERSION"
else
    check_fail "AWS CLI not installed"
fi

echo ""
echo "9. Node.js"
echo "-----------"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js installed: $NODE_VERSION"
else
    check_warn "Node.js not installed"
fi

echo ""
echo "10. Git"
echo "-------"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    check_pass "Git installed: $GIT_VERSION"
else
    check_fail "Git not installed"
fi

echo ""
echo "11. Environment Variables"
echo "-------------------------"
if [ -f /workshop/.env ]; then
    check_pass ".env file exists"
    
    if grep -q "AWS_REGION" /workshop/.env; then
        check_pass "AWS_REGION configured"
    else
        check_warn "AWS_REGION not in .env"
    fi
else
    check_warn ".env file not created"
fi

echo ""
echo "12. Workshop Stack Configuration"
echo "---------------------------------"
if [ -n "$WORKSHOP_STACK_NAME" ]; then
    check_pass "WORKSHOP_STACK_NAME set: $WORKSHOP_STACK_NAME"
else
    check_warn "WORKSHOP_STACK_NAME not set"
fi

echo ""
echo "13. Database Environment Variables"
echo "-----------------------------------"
# Check main database variables
if [ -n "$RDS_CLUSTER_ARN" ]; then
    check_pass "RDS_CLUSTER_ARN configured"
else
    check_warn "RDS_CLUSTER_ARN not set"
fi

if [ -n "$RDS_SECRET_ARN" ] || [ -n "$MAIN_SECRET_ARN" ]; then
    check_pass "Main database secret ARN configured"
else
    check_warn "Main database secret ARN not set"
fi

if [ -n "$PGHOST" ]; then
    check_pass "PostgreSQL connection variables set (PGHOST: $PGHOST)"
else
    check_warn "PostgreSQL connection variables not set"
fi

echo ""
echo "14. IDR Database Configuration"
echo "-------------------------------"
if [ -n "$IDR_CLUSTER_ARN" ]; then
    check_pass "IDR_CLUSTER_ARN configured"
else
    check_warn "IDR_CLUSTER_ARN not set (may not be deployed)"
fi

if [ -n "$IDR_SECRET_ARN" ]; then
    check_pass "IDR ACU secret ARN configured"
else
    check_warn "IDR ACU secret ARN not set (may not be deployed)"
fi

if [ -n "$IOPS_SECRET_ARN" ]; then
    check_pass "IDR IOPS secret ARN configured"
else
    check_warn "IDR IOPS secret ARN not set (may not be deployed)"
fi

echo ""
echo "15. Knowledge Base Configuration"
echo "---------------------------------"
if [ -n "$MAIN_KB_ID" ]; then
    check_pass "Main Knowledge Base ID configured: $MAIN_KB_ID"
else
    check_warn "Main Knowledge Base ID not set"
fi

echo ""
echo "16. DynamoDB Configuration"
echo "--------------------------"
if [ -n "$DYNAMODB_TABLE" ] || [ -n "$INCIDENT_TABLE" ]; then
    check_pass "DynamoDB incident table configured"
else
    check_warn "DynamoDB incident table not set (may not be deployed)"
fi

echo ""
echo "17. Cognito Configuration"
echo "-------------------------"
if [ -n "$COGNITO_USER_POOL_ID" ]; then
    check_pass "Cognito User Pool ID configured"
else
    check_warn "Cognito User Pool ID not set"
fi

if [ -n "$COGNITO_CLIENT_ID" ]; then
    check_pass "Cognito Client ID configured"
else
    check_warn "Cognito Client ID not set"
fi

echo ""
echo "18. PostgreSQL Connection Functions"
echo "------------------------------------"
if grep -q "function psql_main()" /home/ec2-user/.bashrc 2>/dev/null; then
    check_pass "psql_main function defined in .bashrc"
else
    check_warn "psql_main function not defined in .bashrc"
fi

if grep -q "function psql_idr_acu()" /home/ec2-user/.bashrc 2>/dev/null; then
    check_pass "psql_idr_acu function defined in .bashrc"
else
    check_warn "psql_idr_acu function not defined (may not be deployed)"
fi

if grep -q "function psql_idr_iops()" /home/ec2-user/.bashrc 2>/dev/null; then
    check_pass "psql_idr_iops function defined in .bashrc"
else
    check_warn "psql_idr_iops function not defined (may not be deployed)"
fi

echo ""
echo "19. Load Testing Aliases"
echo "------------------------"
if grep -q "alias iops-test=" /home/ec2-user/.bashrc 2>/dev/null; then
    check_pass "iops-test alias defined in .bashrc"
else
    check_warn "iops-test alias not defined"
fi

if grep -q "alias acu-test=" /home/ec2-user/.bashrc 2>/dev/null; then
    check_pass "acu-test alias defined in .bashrc"
else
    check_warn "acu-test alias not defined"
fi

if grep -q "alias main-test=" /home/ec2-user/.bashrc 2>/dev/null; then
    check_pass "main-test alias defined in .bashrc"
else
    check_warn "main-test alias not defined"
fi

echo ""
echo "20. Mahavat Agent Setup"
echo "-----------------------"
if [ -d /workshop/mahavat_agent ]; then
    check_pass "Mahavat agent directory exists"
    
    if [ -d /workshop/mahavat_agent/venv ]; then
        check_pass "Mahavat agent virtual environment exists"
        
        # Check if strands packages are installed
        if /workshop/mahavat_agent/venv/bin/pip list 2>/dev/null | grep -q "strands-agents"; then
            check_pass "Strands agents package installed"
        else
            check_warn "Strands agents package not installed"
        fi
    else
        check_warn "Mahavat agent virtual environment not created"
    fi
else
    check_warn "Mahavat agent directory not found"
fi

echo ""
echo "21. Load Testing Scripts"
echo "------------------------"
if [ -f /workshop/load-test/run_stress_test.sh ]; then
    check_pass "Load testing scripts available"
else
    check_warn "Load testing scripts not found"
fi

echo ""
echo "============================================"
echo "Validation Summary"
echo "============================================"
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Environment validation passed!${NC}"
    echo ""
    echo "To view all workshop environment variables, run: workshop-env"
    exit 0
else
    echo -e "${RED}❌ Environment validation failed with $ERRORS error(s)${NC}"
    exit 1
fi
