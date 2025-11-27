#!/bin/bash

################################################################################
# Mahavat Agent V1 (IDR Agent) Startup Script
# Description: Validates environment and launches the IDR Agent Streamlit app
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

################################################################################
# Configuration
################################################################################

readonly SCRIPT_NAME="Mahavat Agent v1"
readonly STREAMLIT_PORT=8502
readonly STREAMLIT_HOST="0.0.0.0"
readonly VENV_PATH="/workshop/mahavat_agent/venv/bin/activate"
readonly APP_SCRIPT="mahavat_agent_v1.py"

################################################################################
# Color Codes for Output
################################################################################

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

################################################################################
# Logging Functions
################################################################################

log_info() {
    echo -e "${CYAN}ℹ️  ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✅ ${NC}$1"
}

log_warning() {
    echo -e "${YELLOW}⚠️  ${NC}$1"
}

log_error() {
    echo -e "${RED}❌ ${NC}$1" >&2
}

log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

################################################################################
# Validation Functions
################################################################################

validate_env_var() {
    local var_name=$1
    local var_value=${!var_name:-}
    
    if [ -z "$var_value" ]; then
        log_error "Environment variable '$var_name' is not set"
        return 1
    fi
    return 0
}

validate_all_env_vars() {
    log_section "Validating Environment Variables"
    
    local all_valid=true
    
    # Required variables for IDR Agent
    local required_vars=(
        "AWS_REGION"
        "IDR_CLUSTER_ARN"
        "IDR_SECRET_ARN"
        "IDR_DATABASE_NAME"
        "DYNAMODB_TABLE"
    )
    
    # Validate all required variables
    for var in "${required_vars[@]}"; do
        if ! validate_env_var "$var"; then
            all_valid=false
        fi
    done
    
    if [ "$all_valid" = false ]; then
        log_error "Environment validation failed. Please set all required variables."
        return 1
    fi
    
    log_success "All environment variables validated"
    return 0
}

display_configuration() {
    log_section "Current Configuration"
    
    echo -e "${CYAN}AWS Configuration:${NC}"
    echo "   Region:              $AWS_REGION"
    echo ""
    
    echo -e "${CYAN}IDR Configuration:${NC}"
    echo "   Cluster ARN:         $IDR_CLUSTER_ARN"
    echo "   Secret ARN:          $IDR_SECRET_ARN"
    echo "   Database:            $IDR_DATABASE_NAME"
    echo ""
    
    echo -e "${CYAN}DynamoDB:${NC}"
    echo "   Table:               $DYNAMODB_TABLE"
    echo ""
    
    echo -e "${CYAN}Application:${NC}"
    echo "   Port:                $STREAMLIT_PORT"
    echo "   Host:                $STREAMLIT_HOST"
}

activate_virtual_environment() {
    log_section "Activating Virtual Environment"
    
    if [ ! -f "$VENV_PATH" ]; then
        log_error "Virtual environment not found at: $VENV_PATH"
        return 1
    fi
    
    # shellcheck disable=SC1090
    source "$VENV_PATH"
    log_success "Virtual environment activated"
}

start_streamlit_app() {
    log_section "Starting $SCRIPT_NAME"
    
    # Kill any existing Streamlit processes
    log_info "Stopping any existing Streamlit applications..."
    pkill -f streamlit || true
    sleep 2
    
    log_info "Launching Streamlit application..."
    log_info "Access URL: ${GREEN}http://localhost:$STREAMLIT_PORT${NC}"
    echo ""
    
    # Start Streamlit with error handling
    if streamlit run "$APP_SCRIPT" \
        --server.port "$STREAMLIT_PORT" \
        --server.address "$STREAMLIT_HOST" \
        --server.headless true \
        --browser.gatherUsageStats false; then
        log_success "$SCRIPT_NAME completed successfully"
    else
        log_error "$SCRIPT_NAME failed to start"
        return 1
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    
    log_section "🚀 Starting $SCRIPT_NAME"
    
    # Validate environment
    if ! validate_all_env_vars; then
        exit 1
    fi
    
    # Display configuration
    display_configuration
    
    # Activate virtual environment
    if ! activate_virtual_environment; then
        exit 1
    fi
    
    # Start the application
    if ! start_streamlit_app; then
        exit 1
    fi
}

################################################################################
# Script Entry Point
################################################################################

# Trap errors and cleanup
trap 'log_error "Script failed on line $LINENO"' ERR

# Run main function
main "$@"
