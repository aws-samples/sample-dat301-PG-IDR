#!/bin/bash

################################################################################
# IOPS Stress Test Script
# Description: Runs I/O intensive stress test on IDR provisioned instance
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

################################################################################
# Configuration
################################################################################

readonly SCRIPT_NAME="IOPS Stress Test"
readonly WORKLOAD_TYPE="IO"
readonly VENV_PATH="/workshop/mahavat_agent/venv/bin/activate"
readonly STRESS_TEST_SCRIPT="/workshop/load-test/stress_test.py"

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
    
    # Required variables for IOPS test
    local required_vars=(
        "IOPS_SECRET_ARN"
        "AWS_REGION"
    )
    
    # Validate all required variables
    for var in "${required_vars[@]}"; do
        if ! validate_env_var "$var"; then
            all_valid=false
        fi
    done
    
    if [ "$all_valid" = false ]; then
        log_error "Environment validation failed. Please set all required variables."
        log_info "Run 'source ~/.bashrc' to load environment variables"
        return 1
    fi
    
    log_success "All environment variables validated"
    return 0
}

display_configuration() {
    log_section "Test Configuration"
    
    echo -e "${CYAN}Target:${NC}"
    echo "   Database:            IDR Provisioned Instance"
    echo "   Secret ARN:          $IOPS_SECRET_ARN"
    echo ""
    
    echo -e "${CYAN}Test Parameters:${NC}"
    echo "   Workload Type:       $WORKLOAD_TYPE (I/O Intensive)"
    echo "   Region:              $AWS_REGION"
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

run_stress_test() {
    log_section "Running $SCRIPT_NAME"
    
    if [ ! -f "$STRESS_TEST_SCRIPT" ]; then
        log_error "Stress test script not found at: $STRESS_TEST_SCRIPT"
        return 1
    fi
    
    log_info "Starting IOPS stress test..."
    log_warning "This test will generate high I/O load on the database"
    log_info "Test will run for approximately 1200 seconds (20 minutes)..."
    echo ""
    
    log_info "⏳ Initializing pgbench tables (if needed)..."
    log_info "⏳ Running I/O intensive queries..."
    log_info "⏳ Monitor CloudWatch for RDS ReadIOPS metrics"
    echo ""
    
    # Run stress test with error handling
    if python3 "$STRESS_TEST_SCRIPT" -s "$IOPS_SECRET_ARN" -w "$WORKLOAD_TYPE"; then
        echo ""
        log_success "IOPS stress test completed successfully"
        log_info "Check CloudWatch alarms for RDS ReadIOPS threshold breaches"
    else
        log_error "IOPS stress test failed"
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
    
    # Run the stress test
    if ! run_stress_test; then
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
