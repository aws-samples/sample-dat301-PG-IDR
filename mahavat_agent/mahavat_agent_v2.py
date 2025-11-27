#!/usr/bin/env python3
"""
Unified Mahavat Agent - Final version with fixed MCP servers and clean UI
"""

import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands_tools import current_time
from mcp import StdioServerParameters, stdio_client
import boto3

# Configuration - Using workshop environment variables
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'dat301-ws-incidents')
MAIN_KB_ID = os.environ.get('MAIN_KB_ID', '')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'workshop_db')
RDS_CLUSTER_ARN = os.environ.get('RDS_CLUSTER_ARN', '')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', '')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID', '')

# Demo user credentials from environment
DEMO_USERNAME = os.environ.get('DEMO_USERNAME', 'demo')
DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD', 'WorkshopDemo2025!')

# Use main database secret ARN for PostgreSQL
DATABASE_SECRET_ARN = os.environ.get('DATABASE_SECRET_ARN', '')
POSTGRES_SECRET_ARN = DATABASE_SECRET_ARN  # Use main DB secret
POSTGRES_RESOURCE_ARN = RDS_CLUSTER_ARN

def authenticate_with_cognito(username: str, password: str) -> tuple[bool, str, dict]:
    """Authenticate user with AWS Cognito
    
    Returns:
        tuple: (success: bool, message: str, tokens: dict)
    """
    try:
        cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
        
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        return True, "Authentication successful!", response.get('AuthenticationResult', {})
    
    except cognito_client.exceptions.NotAuthorizedException:
        return False, "Invalid username or password", {}
    except cognito_client.exceptions.UserNotFoundException:
        return False, "User not found", {}
    except Exception as e:
        return False, f"Authentication error: {str(e)}", {}

def show_login_page():
    """Display full-screen login page for demo user"""
    
    # Custom CSS
    st.markdown("""
        <style>
        .header-flex {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;
        }
        .header-flex img {
            width: 108px;
            height: 135px;
        }
        .header-text h1 {
            margin: 0;
            font-size: 2rem;
            color: #232F3E;
        }
        .header-text p {
            margin: 5px 0 0 0;
            color: #545B64;
        }
        .feature-badge {
            display: inline-block;
            background: #F0F8FF;
            color: #0073BB;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            margin: 4px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center everything
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Header with logo and title using HTML flexbox
        try:
            import base64
            with open("Mahavat-agent.png", "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            
            st.markdown(f"""
                <div class="header-flex">
                    <img src="data:image/png;base64,{img_data}" alt="Mahavat Logo">
                    <div class="header-text">
                        <h1>Mahavat Agent v2</h1>
                        <p><strong>Unified PostgreSQL & IDR Agent</strong></p>
                        <p style="font-size: 0.9rem; color: #879596;">Powered by Amazon Aurora & Amazon Bedrock</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("""
                <div class="header-flex">
                    <div style="font-size: 3rem;">🐘</div>
                    <div class="header-text">
                        <h1>Mahavat Agent v2</h1>
                        <p><strong>Unified PostgreSQL & IDR Agent</strong></p>
                        <p style="font-size: 0.9rem; color: #879596;">Powered by Amazon Aurora & Amazon Bedrock</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Login section
        st.markdown("### 🎯 Workshop Access")
        st.markdown("Welcome to the DAT301 Workshop. Click below to access the Mahavat Agent with demo credentials.")
        
        st.markdown("")
        
        if st.button("🔐 Login with Demo User", use_container_width=True, type="primary", key="login_button"):
            with st.spinner("🔄 Authenticating with AWS Cognito..."):
                success, message, tokens = authenticate_with_cognito(DEMO_USERNAME, DEMO_PASSWORD)
                
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = DEMO_USERNAME
                    st.session_state.auth_tokens = tokens
                    st.session_state.login_time = datetime.now()
                    st.success(f"✅ {message}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        # Features
        st.markdown("")
        st.markdown("#### ✨ Key Features")
        st.markdown("""
        <div style='text-align: center;'>
            <span class='feature-badge'>🐘 PostgreSQL Diagnostics</span>
            <span class='feature-badge'>🚨 Incident Detection</span>
            <span class='feature-badge'>📋 Runbook Automation</span>
            <span class='feature-badge'>☁️ AWS Integration</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Workshop info
        st.markdown("")
        with st.expander("ℹ️ Workshop Information"):
            st.markdown(f"""
            **Session Details:**
            - **Username:** `{DEMO_USERNAME}`
            - **Authentication:** AWS Cognito
            - **Access Level:** Full workshop access
            - **Session Duration:** Active until browser close
            
            **Environment Configuration:**
            - **Region:** `{AWS_REGION}`
            - **DynamoDB Table:** `{DYNAMODB_TABLE}`
            - **Knowledge Base ID:** `{MAIN_KB_ID}`
            
            **Capabilities:**
            - ✅ PostgreSQL performance diagnostics and optimization
            - ✅ Automated incident detection and remediation
            - ✅ Runbook-driven workflow execution
            - ✅ AWS resource management and monitoring
            - ✅ Real-time incident status tracking
            - ✅ Integration with Amazon Bedrock for AI-powered analysis
            """)

def get_kpi(iconname, metricname, metricvalue):
    """Create KPI card"""
    wch_colour_box = (0,204,102)
    wch_colour_font = (0,0,0)
    fontsize = 32
    lnk = '<link rel="stylesheet" href="https://use.fontawesome.com/releases/v6.6.0/css/all.css" crossorigin="anonymous">'
    
    htmlstr = f"""<p style='background-color: rgb({wch_colour_box[0]}, 
                                              {wch_colour_box[1]}, 
                                              {wch_colour_box[2]}, 0.75); 
                        color: rgb({wch_colour_font[0]}, 
                                   {wch_colour_font[1]}, 
                                   {wch_colour_font[2]}, 0.75); 
                        font-size: {fontsize}px; 
                        border-radius: 7px; 
                        padding-left: 12px; 
                        padding-top: 18px; 
                        padding-bottom: 18px; 
                        line-height:25px;'>
                        <i class='{iconname} fa-xs'></i> {metricvalue}
                        </style><BR><span style='font-size: 14px; 
                        margin-top: 0;'>{metricname}</style></span></p>"""
    return lnk + htmlstr

def create_mcp_client_safe(name, server_params, status_container):
    """Safely create MCP client with error handling - messages in sidebar"""
    try:
        with status_container:
            st.info(f"🔄 Initializing {name}...")
        client = MCPClient(lambda: stdio_client(server_params))
        client.start()
        with status_container:
            st.success(f"✅ {name}")
        return client
    except Exception as e:
        with status_container:
            st.warning(f"⚠️ {name}: {str(e)[:50]}...")
        return None

@st.cache_resource
def create_available_mcp_clients():
    """Initialize available MCP clients - messages in sidebar only"""
    
    # Create a placeholder in sidebar for status messages
    with st.sidebar:
        status_container = st.empty()
        with status_container:
            st.info("🔧 Initializing MCP servers...")
    
    available_clients = {}
    
    # MCP server configurations with correct package names
    mcp_configs = {
        'idr': {
            'params': StdioServerParameters(
                command="python3",
                args=[os.path.join(os.path.dirname(__file__), "idr_mcp_server.py")],
                env={
                    "AWS_REGION": AWS_REGION,
                    "DYNAMODB_TABLE": DYNAMODB_TABLE
                }
            ),
            'required': True,
            'description': 'Incident management'
        },
        'main_kb': {
            'params': StdioServerParameters(
                command="uvx",
                args=["awslabs.bedrock-kb-retrieval-mcp-server@latest"],
                env={
                    "AWS_REGION": AWS_REGION,
                    "FASTMCP_LOG_LEVEL": "ERROR"
                }
            ),
            'required': True,
            'description': 'Knowledge base retrieval'
        },
        'aws_api': {
            'params': StdioServerParameters(
                command="uvx",
                args=["awslabs.aws-api-mcp-server@latest", "--region", AWS_REGION],
                env={"AWS_REGION": AWS_REGION}
            ),
            'required': True,
            'description': 'AWS operations'
        },
        'cloudwatch': {
            'params': StdioServerParameters(
                command="uvx",
                args=["awslabs.cloudwatch-mcp-server@latest"],
                env={
                    "AWS_REGION": AWS_REGION,
                    "FASTMCP_LOG_LEVEL": "ERROR"
                }
            ),
            'required': True,
            'description': 'CloudWatch logs and metrics'
        },
        'performance_insights': {
            'params': StdioServerParameters(
                command="python3",
                args=[os.path.join(os.path.dirname(__file__), "pi_mcp_server.py")],
                env={"AWS_REGION": AWS_REGION}
            ),
            'required': True,
            'description': 'RDS Performance Insights (Dynamic)'
        },
        'aws_docs': {
            'params': StdioServerParameters(
                command="uvx",
                args=["awslabs.aws-documentation-mcp-server@latest"],  # Correct package name
                env={
                    "AWS_REGION": AWS_REGION,
                    "FASTMCP_LOG_LEVEL": "ERROR"
                }
            ),
            'required': True,
            'description': 'AWS documentation'
        }
    }
    
    # Add PostgreSQL server with main DB secret
    if POSTGRES_SECRET_ARN and POSTGRES_RESOURCE_ARN:
        mcp_configs['postgres'] = {
            'params': StdioServerParameters(
                command="uvx",
                args=[
                    "awslabs.postgres-mcp-server@latest",
                    "--secret_arn", POSTGRES_SECRET_ARN,
                    "--database", DATABASE_NAME,
                    "--region", AWS_REGION,
                    "--readonly", "false",
                    "--resource_arn", POSTGRES_RESOURCE_ARN
                ],
                env={"AWS_REGION": AWS_REGION}
            ),
            'required': True,
            'description': 'PostgreSQL database access'
        }
    
    # Add postgres query provider if file exists
    provider_file = os.path.join(os.path.dirname(__file__), "postgres_query_provider.py")
    if os.path.exists(provider_file):
        mcp_configs['postgres_query_provider'] = {
            'params': StdioServerParameters(
                command="python3",
                args=[provider_file],
                env={"AWS_REGION": AWS_REGION}
            ),
            'required': True,
            'description': 'PostgreSQL diagnostic workflows'
        }
    
    # Initialize each client - status messages in sidebar
    for name, config in mcp_configs.items():
        client = create_mcp_client_safe(name, config['params'], status_container)
        if client:
            available_clients[name] = client
        elif config['required']:
            with status_container:
                st.error(f"❌ Required server '{name}' failed")
    
    # Final status in sidebar
    with status_container:
        st.success(f"✅ {len(available_clients)} MCP servers initialized")
    
    return available_clients

# Global MCP clients (initialized after authentication)
# Moved to main() function to avoid loading before login

# Create standard tools list
standard_tools = [current_time]

@tool
def postgres_diagnostic_specialist(
    query: str, 
    context: str = "",
    enable_streaming: bool = True,
    workshop_mode: bool = False
) -> str:
    """PostgreSQL diagnostic specialist with available MCP servers."""
    
    # Get mcp_clients from session state
    mcp_clients = st.session_state.get('mcp_clients', {})
    
    # Get available PostgreSQL MCP tools
    postgres_mcp_tools = []
    postgres_servers = ['postgres_query_provider', 'postgres', 'performance_insights', 
                       'cloudwatch', 'aws_api', 'aws_docs', 'main_kb']
    
    for server_name in postgres_servers:
        if server_name in mcp_clients and mcp_clients[server_name]:
            try:
                tools = mcp_clients[server_name].list_tools_sync()
                postgres_mcp_tools.extend(tools)
            except Exception as e:
                pass  # Silent failure for tool loading
    
    if not postgres_mcp_tools:
        return "PostgreSQL diagnostic tools are not available. Please check MCP server initialization."
    
    # PostgreSQL system prompt with standardized formatting
    postgres_system_prompt = f"""You are a PostgreSQL Database expert with comprehensive MCP server access.

**Available MCP Servers:** {list(mcp_clients.keys())}

**MANDATORY OUTPUT FORMATTING:**

For database analysis, ALWAYS use this EXACT format with smaller headers:

### Comprehensive Analysis

#### Executive Summary
- **Root Cause:** [Database issue identification]
- **Impact:** [Performance/availability impact]
- **Current Constraint:** [Resource/configuration limits]
- **Health Status:** [Critical/Degraded/Warning/Healthy]

#### Key Findings from Multi-Tool Analysis

##### AWS API Analysis
- **Cluster Status:** [RDS cluster state]
- **Configuration:** [Database parameters]
- **Resource Utilization:** [CPU/Memory/Storage]

##### Performance Insights Results
- **Metrics Status:** [PI availability]
- **Top Wait Events:** [Blocking events]
- **SQL Performance:** [Query performance data]

##### PostgreSQL Diagnostics (via RDS Data API)
- **Problematic Query:** [Slow/blocking queries]
- **Query Cost:** [Execution plans/costs]
- **Active PIDs:** [Session information]
- **Connection Count:** [Active connections]

##### CloudWatch Analysis
- **Database Metrics:** [CPU/Memory trends]
- **Log Insights:** [Error patterns]
- **Performance Trends:** [Historical data]

#### Recommendations
[Specific database optimization recommendations]

**WORKFLOW-FIRST Approach:**
• vacuum/bloat/autovacuum → vacuum_analysis_diagnostic()
• slow queries/performance → query_performance_diagnostic()
• locks/blocking → lock_analysis_diagnostic()
• connections/sessions → connection_analysis_diagnostic()

**Multi-Server Capabilities:**
• PostgreSQL: Direct SQL execution and database analysis
• Performance Insights: RDS metrics and top SQL queries (use get_performance_insights_metrics, get_top_sql_statements, get_wait_events)
• CloudWatch: Log analysis and infrastructure metrics (Default: /aws/rds/cluster/dat301-ws-cluster/postgresql)
• AWS API: RDS configuration and parameter analysis
• AWS Docs: Best practices and troubleshooting guides
• Main KB: Runbook retrieval (ID: {MAIN_KB_ID})

**Performance Insights Workflow (CRITICAL):**
1. **ALWAYS call get_cluster_identifier() FIRST** to get the instance identifier:
   result = get_cluster_identifier(cluster_name="dat301-ws-cluster")
   instance_id = result["writer_instance"]

2. Then use that instance_id with PI tools:
   - get_wait_events(cluster_identifier=instance_id)
   - get_top_sql_statements(cluster_identifier=instance_id)
   - get_performance_insights_metrics(cluster_identifier=instance_id)

3. Example complete workflow:
   Step 1: cluster_info = get_cluster_identifier(cluster_name="dat301-ws-cluster")
   Step 2: wait_events = get_wait_events(cluster_identifier=cluster_info["writer_instance"])

4. If you get an error about missing cluster_identifier, you forgot Step 1!

**Query Tools (Use Instead of Raw SQL):**
• get_index_statistics(index_names=[...]) - Get statistics for specific indexes
• get_table_statistics(table_name="...") - Get statistics for a specific table

**Aurora PostgreSQL - System Database Filtering:**
- Aurora uses 'rdsadmin' database and user for internal maintenance
- ALWAYS exclude these from analysis to focus on user activity
- Apply these filters in ALL queries:
  * pg_stat_activity: WHERE datname != 'rdsadmin' AND usename != 'rdsadmin'
  * pg_stat_database: WHERE datname NOT IN ('rdsadmin', 'template0', 'template1')
  * pg_locks: JOIN to pg_stat_activity and apply same filters
  * Query analysis: Ignore queries from rdsadmin user

**CRITICAL Rules:**
- Use all available tools for comprehensive analysis
- ALWAYS include --region {AWS_REGION} in AWS commands
- You are running postgresql version 17
- For CloudWatch: Use default log group /aws/rds/cluster/dat301-ws-cluster/postgresql unless user specifies otherwise
- Confirm log group with user if needed: "I'll analyze logs from /aws/rds/cluster/dat301-ws-cluster/postgresql. Is this correct?"
- Provide multi-dimensional analysis combining database + infrastructure data
- Execute parallel analysis across multiple MCP servers when possible
- **NEVER recommend or execute VACUUM FULL** - it locks tables and causes downtime
- **NEVER create or drop indexes unless explicitly asked by the user**

**⚠️ COST DISCLAIMER:**
- **BEFORE making ANY infrastructure changes** (modify-db-instance, modify-db-cluster, scaling, etc.), ALWAYS warn the user:
  "⚠️ WARNING: This change will modify AWS infrastructure and may incur additional costs. The modification includes [describe change]."
- This applies to: instance class changes, ACU scaling, parameter changes, etc.

**AWS CLI Command Validation (CRITICAL):**
- BEFORE calling call_aws, verify:
  * All parameters have values (no empty --param without value)
  * JSON structures use correct AWS field names (check AWS CLI docs)
  * Use dedicated MCP tools when available instead of call_aws
- For Performance Insights: ALWAYS use get_performance_insights_metrics(), get_top_sql_statements(), get_wait_events() tools
- For RDS Data API: Use secret NAME not full ARN (e.g., "my-secret" not "arn:aws:secretsmanager:...")
- If call_aws fails with validation error, use dedicated MCP tool instead

**Query Validation (CRITICAL):**
- BEFORE executing queries with run_query(), verify:
  * No empty IN clauses: WHERE col IN () ❌
  * No placeholder values: WHERE col = '<placeholder>' or WHERE col = '< Add value >' ❌
  * All parameters have actual values from user or context
- For pg_stat queries, use dedicated tools:
  * get_index_statistics(index_names=["idx1", "idx2"]) instead of raw pg_stat_user_indexes
  * get_table_statistics(table_name="actual_table") instead of raw pg_stat_user_tables
- If query needs parameters, ask user for actual values first

DATABASE: {DATABASE_NAME}, REGION: {AWS_REGION}
"""
    
    # Create PostgreSQL specialist agent
    postgres_agent = Agent(
        name="PostgreSQL_Diagnostic_Specialist",
        model=BedrockModel(model_id=BEDROCK_MODEL_ID),
        tools=postgres_mcp_tools + standard_tools,
        system_prompt=postgres_system_prompt
    )
    
    enhanced_prompt = f"""
CONTEXT: {context}
USER QUERY: {query}

Available servers: {list(mcp_clients.keys())}
Total tools: {len(postgres_mcp_tools)}

Execute comprehensive PostgreSQL diagnostics using all available MCP servers:
- Use workflow detection if postgres_query_provider available
- Execute SQL queries if postgres server available  
- Get Performance Insights metrics if available
- Search CloudWatch logs if available
- Check AWS configuration if aws_api available
- Retrieve runbooks from Main KB if available

Provide multi-server analysis with actionable recommendations.
"""
    
    try:
        return str(postgres_agent(enhanced_prompt))
    except Exception as e:
        return f"PostgreSQL diagnostic error: {str(e)}"

@tool
def idr_incident_specialist(
    incident_context: str,
    action: str,
    incident_data: dict = None
) -> str:
    """IDR specialist with available MCP servers."""
    
    # Get mcp_clients from session state
    mcp_clients = st.session_state.get('mcp_clients', {})
    
    # Get available IDR MCP tools
    idr_mcp_tools = []
    idr_servers = ['idr', 'main_kb', 'aws_api']
    
    for server_name in idr_servers:
        if server_name in mcp_clients and mcp_clients[server_name]:
            try:
                tools = mcp_clients[server_name].list_tools_sync()
                idr_mcp_tools.extend(tools)
            except Exception as e:
                pass  # Silent failure for tool loading
    
    if not idr_mcp_tools:
        return "IDR tools are not available. Please check MCP server initialization."
    
    # IDR system prompt with standardized formatting
    idr_system_prompt = f"""You are an AWS incident analysis and remediation specialist.

**Available MCP Servers:** {list(mcp_clients.keys())}

**MANDATORY OUTPUT FORMATTING:**

For runbook analysis, ALWAYS use this EXACT format with smaller headers:

### Comprehensive Analysis

#### Executive Summary
- **Root Cause:** [Identify the primary cause]
- **Impact:** [Describe business/service impact]  
- **Current Constraint:** [Identify limiting factors]
- **Health Status:** [Critical/Degraded/Warning/Healthy]

#### Key Findings from Multi-Tool Analysis

##### AWS API Analysis
- **Cluster Status:** [Available/Modifying/Failed]
- **Configuration:** [Key config details]
- **Resource Utilization:** [Current usage metrics]

##### Performance Insights Results
- **Metrics Status:** [Enabled/Disabled/Error]
- **Top Wait Events:** [If available]
- **SQL Performance:** [If available]

##### PostgreSQL Diagnostics (via RDS Data API)
- **Problematic Query:** [Identify resource-intensive queries]
- **Query Cost:** [Execution cost analysis]
- **Active PIDs:** [Running process IDs]
- **Connection Count:** [Active connections]

##### CloudWatch Analysis
- **ACU Utilization:** [Current and peak usage]
- **IOPS Utilization:** [Current and peak usage]
- **CPU Metrics:** [CPU utilization patterns]
- **Log Insights:** [Relevant log findings]

#### Recommendations
[Specific actionable recommendations]

For remediation, ALWAYS use this EXACT format:

### Incident Remediation Summary

#### Actions Completed
- ✅ [Action 1 with specific details]
- ✅ [Action 2 with specific details]
- ✅ [Action 3 with specific details]

#### Incident Details
- **Incident ID:** [ID from system]
- **Status:** [RESOLVED/IN_PROGRESS/FAILED]
- **Completion Time:** [Timestamp]

#### Relevant Details
- **Cluster Name:** [Target cluster]
- **Changes Made:** [Specific modifications]
- **Verification Status:** [Post-remediation checks]

**Capabilities:**
• IDR Server: Incident management (list, details, status updates)
• Main KB: Runbook retrieval from knowledge base (ID: {MAIN_KB_ID})
• AWS API: Resource modifications and verification
• PostgreSQL: Database diagnostics and performance analysis
• Performance Insights: RDS metrics and query analysis
• CloudWatch: Log analysis and infrastructure metrics

**Aurora PostgreSQL - System Database Filtering:**
- Aurora uses 'rdsadmin' database and user for internal maintenance
- ALWAYS exclude these from analysis to focus on user activity
- Apply these filters in ALL queries:
  * pg_stat_activity: WHERE datname != 'rdsadmin' AND usename != 'rdsadmin'
  * pg_stat_database: WHERE datname NOT IN ('rdsadmin', 'template0', 'template1')
  * Query analysis: Ignore queries from rdsadmin user

**Performance Insights Workflow (CRITICAL):**
1. **ALWAYS call get_cluster_identifier() FIRST** to get the instance identifier:
   result = get_cluster_identifier(cluster_name="dat301-ws-cluster")
   instance_id = result["writer_instance"]

2. Then use that instance_id with PI tools:
   - get_wait_events(cluster_identifier=instance_id)
   - get_top_sql_statements(cluster_identifier=instance_id)
   - get_performance_insights_metrics(cluster_identifier=instance_id)

3. Example complete workflow:
   Step 1: cluster_info = get_cluster_identifier(cluster_name="dat301-ws-cluster")
   Step 2: wait_events = get_wait_events(cluster_identifier=cluster_info["writer_instance"])

4. If you get an error about missing cluster_identifier, you forgot Step 1!

**CRITICAL Rules:**
- Follow runbook procedures exactly when available
- ALWAYS include --region {AWS_REGION} in AWS commands
- **NEVER recommend or execute VACUUM FULL** - it locks tables and causes downtime
- **NEVER terminate database connections without explicit user confirmation** - always ask first
- **NEVER create or drop indexes unless explicitly asked by the user**

**⚠️ COST DISCLAIMER:**
- **BEFORE making ANY infrastructure changes** (modify-db-instance, modify-db-cluster, scaling, etc.), ALWAYS warn the user:
  "⚠️ WARNING: This change will modify AWS infrastructure and may incur additional costs. The modification includes [describe change]. Do you want to proceed?"
- Wait for explicit user confirmation before executing infrastructure modifications
- This applies to: instance class changes, ACU scaling, parameter changes, etc.

**AWS CLI Command Validation (CRITICAL):**
- BEFORE calling call_aws, verify:
  * All parameters have values (no empty --param without value)
  * JSON structures use correct AWS field names
  * Use dedicated MCP tools when available instead of call_aws
- For Performance Insights: ALWAYS use get_performance_insights_metrics(), get_top_sql_statements(), get_wait_events() tools
- For RDS Data API: Use secret NAME not full ARN (e.g., "my-secret" not "arn:aws:secretsmanager:...")
- If call_aws fails with validation error, use dedicated MCP tool instead
- For comprehensive analysis: Use ALL available tools (PostgreSQL diagnostics, Performance Insights, CloudWatch logs, runbooks)
- For IDR incidents: Use BOTH local MCP servers AND AWS API for complete analysis:
  * Use postgres_query_provider for database diagnostic workflows
  * Use get_performance_insights_metrics(cluster_identifier="target-instance") for Performance Insights metrics
  * Use get_top_sql_statements(cluster_identifier="target-instance") for top queries
  * Use get_wait_events(cluster_identifier="target-instance") for wait event analysis
  * Use PostgreSQL MCP with RDS Data API for direct database queries on target instance
  * Use CloudWatch MCP for metrics and logs from target cluster
  * Use AWS API for cluster configuration and log group discovery
- For runbook requests: Provide detailed multi-tool analysis AND runbook steps but DO NOT execute remediation
- For chat remediation requests: Ask user "Should I proceed with remediation based on this analysis?" before taking action
- For direct remediation requests: Execute remediation steps immediately to resolve the incident
- Verify all changes before updating incident status
- Combine data from multiple sources for comprehensive insights

**IDR Dynamic Instance Targeting:**
1. Extract cluster/instance name from incidentIdentifier
2. Use AWS API MCP to get cluster ARN and database details for target cluster
3. For RDS Data API queries, use secret NAME (not full ARN) to avoid length validation errors:
   - Example: aws rds-data execute-statement --resource-arn <cluster-arn> --secret-arn my-secret-name --database postgres --sql "SELECT version()"
   - DO NOT use full secret ARN (too long for CLI validation)
4. Use get_performance_insights_metrics(cluster_identifier="target-instance") for PI metrics
5. Use get_top_sql_statements(cluster_identifier="target-instance") for top queries
6. Use get_wait_events(cluster_identifier="target-instance") for wait events
7. Use CloudWatch MCP for cluster-specific metrics and log groups (get correct log group from AWS API)
8. Use PostgreSQL MCP ONLY for runbook queries from main database
9. Combine all data sources for comprehensive incident analysis

**Key Instructions for IDR Tools:**
- AWS API MCP: Get cluster config, discover log groups (avoid RDS Data API due to secret ARN length limits)
- Performance Insights: ALWAYS use get_performance_insights_metrics(cluster_identifier="..."), get_top_sql_statements(cluster_identifier="..."), get_wait_events(cluster_identifier="...") - DO NOT use call_aws for PI queries
- CloudWatch MCP: Use describe_log_groups and execute_log_insights_query with discovered log groups
- Main KB: Retrieve and display runbook content prominently after the executive summary
- DO NOT USE: PostgreSQL MCP server or postgres_query_provider (wrong database/not needed for IDR runbook)

DATABASE: {DATABASE_NAME}, REGION: {AWS_REGION}
DYNAMODB_TABLE: {DYNAMODB_TABLE}
"""
    
    # Create IDR specialist agent
    idr_agent = Agent(
        name="IDR_Incident_Specialist",
        model=BedrockModel(model_id=BEDROCK_MODEL_ID),
        tools=idr_mcp_tools + standard_tools,
        system_prompt=idr_system_prompt
    )
    
    enhanced_prompt = f"""
INCIDENT CONTEXT: {incident_context}
ACTION REQUESTED: {action}
INCIDENT DATA: {incident_data}

Available servers: {list(mcp_clients.keys())}

Execute IDR tasks:
- Use IDR server for incident management if available
- Use Main KB (ID: {MAIN_KB_ID}) for runbooks if available
- Use AWS API for resource modifications if available

Provide comprehensive remediation guidance.
"""
    
    try:
        return str(idr_agent(enhanced_prompt))
    except Exception as e:
        return f"IDR specialist error: {str(e)}"

def create_unified_mahavat_agent():
    """Create unified Mahavat agent with intelligent routing and direct MCP tool access"""
    
    # Get mcp_clients from session state
    mcp_clients = st.session_state.get('mcp_clients', {})
    
    available_servers = list(mcp_clients.keys())
    
    # Get all available MCP tools for direct access
    all_mcp_tools = []
    for server_name in available_servers:
        if server_name in mcp_clients and mcp_clients[server_name]:
            try:
                tools = mcp_clients[server_name].list_tools_sync()
                all_mcp_tools.extend(tools)
            except Exception as e:
                pass  # Silent failure for tool loading
    
    unified_system_prompt = f"""You are the Mahavat Agent - an intelligent AWS database management router with direct MCP tool access.

**Environment:**
- AWS Region: {AWS_REGION}
- Database: {DATABASE_NAME}
- DynamoDB: {DYNAMODB_TABLE}
- Main KB: {MAIN_KB_ID}

**Available MCP Servers ({len(available_servers)}):** {available_servers}
**Total Available Tools:** {len(all_mcp_tools) + 2} (Specialists + MCP Tools)

**INTELLIGENT ROUTING:**

**Route to SPECIALISTS for diagnostic analysis (preserves curated workflows):**
- Queries about **performance problems, slowness, optimization**
- Queries about **database issues, troubleshooting, analysis** 
- Queries requesting **incident remediation or comprehensive analysis**
- Any query that requires **multi-step diagnostic workflows**

**Handle LOCALLY with direct MCP tools for simple operations:**
- Queries requesting **basic information retrieval** (list, show, get)
- Queries for **simple data lookups** without analysis
- Queries about **system status or configuration** without diagnostics

**ROUTING DECISION LOGIC:**
- **Analyze query intent**: Does it seek diagnosis/analysis or just information?
- **Assess complexity**: Does it require workflows or single tool calls?
- **Performance/diagnostic keywords**: Route to postgres_diagnostic_specialist for curated workflows
- **Incident/remediation keywords**: Route to idr_incident_specialist for comprehensive analysis
- **When uncertain**: Default to specialist routing to ensure workflow enforcement
- Simple informational queries: Handle locally with direct MCP tool calls

**Specialist Tools Available:**
1. 🚨 idr_incident_specialist - complex incident workflows, remediation, comprehensive analysis with aggressive prompts
2. 🐘 postgres_diagnostic_specialist - complex database diagnostics with curated workflows and aggressive prompts

**Aurora PostgreSQL - System Database Filtering:**
- Aurora uses 'rdsadmin' database and user for internal maintenance
- ALWAYS exclude these from analysis to focus on user activity
- Apply filters: WHERE datname != 'rdsadmin' AND usename != 'rdsadmin'

**CONTEXT SHARING:**
- Maintain full conversation context across all interactions
- Share incident details between router and specialists
- Pass relevant context when routing to specialists
- Coordinate between specialists for comprehensive solutions
- Preserve conversation history for follow-up questions

**ROUTING DECISION LOGIC:**
- **Analyze query intent using LLM reasoning**: Does it seek diagnosis/analysis or just information?
- **Assess complexity dynamically**: Does it require workflows or single tool calls?
- **Performance/diagnostic intent**: Route to postgres_diagnostic_specialist for curated workflows
- **Incident/remediation intent**: Route to idr_incident_specialist for comprehensive analysis
- **Default to specialist routing when uncertain**: Ensures workflow enforcement over ad-hoc responses
- **Simple informational intent**: Handle locally with direct MCP tool calls
- Preserve specialist aggressive prompts for comprehensive analysis
- For IDR incidents: Use IDR specialist ONLY, do not combine with PostgreSQL specialist

**CRITICAL Rules:**
- Always include --region {AWS_REGION} in AWS commands
- For simple queries: Execute minimal tool calls and provide direct answers
- For complex diagnostics: Route to specialists to enforce curated workflows and comprehensive analysis
- Maintain conversation context across all levels of interaction
- Combine data from multiple sources when appropriate
- **NEVER recommend or execute VACUUM FULL** - it locks tables and causes downtime
- **NEVER terminate database connections without explicit user confirmation** - always ask first
- **NEVER create or drop indexes unless explicitly asked by the user**

**⚠️ COST DISCLAIMER:**
- **BEFORE making ANY infrastructure changes** (modify-db-instance, modify-db-cluster, scaling, etc.), ALWAYS warn the user:
  "⚠️ WARNING: This change will modify AWS infrastructure and may incur additional costs. The modification includes [describe change]."
- This applies to: instance class changes, ACU scaling, parameter changes, etc.

**AWS CLI Command Validation (CRITICAL):**
- BEFORE calling call_aws, verify:
  * All parameters have values (no empty --param without value)
  * JSON structures use correct AWS field names
  * Use dedicated MCP tools when available instead of call_aws
- For Performance Insights: ALWAYS use get_performance_insights_metrics(), get_top_sql_statements(), get_wait_events() tools
- For RDS Data API: Use secret NAME not full ARN (e.g., "my-secret" not "arn:aws:secretsmanager:...")
- If call_aws fails with validation error, use dedicated MCP tool instead

**Query Validation (CRITICAL):**
- BEFORE executing queries, verify:
  * No empty IN clauses or placeholder values
  * Use get_index_statistics() and get_table_statistics() for pg_stat queries
  * Ask user for actual values if parameters are missing
"""
    
    unified_agent = Agent(
        name="Mahavat_Agent",
        model=BedrockModel(model_id=BEDROCK_MODEL_ID),
        tools=[
            postgres_diagnostic_specialist,
            idr_incident_specialist
        ] + all_mcp_tools + standard_tools,
        system_prompt=unified_system_prompt
    )
    
    return unified_agent

def get_incidents_data(status="PENDING"):
    """Get incidents from DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        if status:
            response = table.scan(
                FilterExpression='incident_status = :status',
                ExpressionAttributeValues={':status': status}
            )
        else:
            response = table.scan()
        
        return response.get('Items', [])
    except Exception as e:
        st.error(f"Error fetching incidents: {str(e)}")
        return []

def handle_chat_message(prompt):
    """Handle chat message from user"""
    
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    
    unified_agent = st.session_state.unified_mahavat_agent
    
    context_prompt = prompt
    if st.session_state.selected_incident_context:
        context_prompt = f"Context: {st.session_state.selected_incident_context}\n\nUser request: {prompt}"
    
    try:
        with st.spinner("Mahavat Agent thinking... (Follow the logs in your terminal to see what the agent is doing in real-time)"):
            response = unified_agent(context_prompt)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": str(response)})
        
    except Exception as e:
        st.session_state.chat_messages.append({
            "role": "assistant", 
            "content": f"Error: {str(e)}"
        })
    
    st.rerun()

def show_pending_incidents():
    """Show pending incidents page"""
    st.title(":orange[Pending Incidents]")
    st.subheader(f":orange[Metric Summary as of] :blue[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]", divider=True)
    
    incidents = get_incidents_data(status="PENDING")
    
    if not incidents:
        st.info("No pending incidents found")
        return
    
    # Prepare dataframe
    incidents_data = []
    for item in incidents:
        incidents_data.append({
            'pk': item.get('pk', ''),
            'incident_id': item.get('incident_id', ''),
            'incidentIdentifier': item.get('incidentIdentifier', item.get('incident_identifier', '')),
            'incidentType': item.get('incidentType', item.get('incident_type', '')),
            'incident_status': item.get('incident_status', ''),
            'incident_time': item.get('incident_time', ''),
            'alarm_name': item.get('alarm_name', ''),
            'alarm_reason': item.get('alarm_reason', '')
        })
    
    df = pd.DataFrame(incidents_data)
    df = df.sort_values('incident_time', ascending=False)
    
    # Display KPIs
    col1, col2, col3 = st.columns(3)
    col1.markdown(get_kpi("fa-solid fa-circle-exclamation", "Total Pending Incidents", len(df)), unsafe_allow_html=True)
    col2.markdown(get_kpi("fa-solid fa-server", "Total Unique Instance", df['incidentIdentifier'].nunique()), unsafe_allow_html=True)
    col3.markdown(get_kpi("fa-solid fa-bell", "Total Unique Alert Type", df['incidentType'].nunique()), unsafe_allow_html=True)
    
    # Incident table and actions
    col4, col5 = st.columns([3, 1])
    
    col4.markdown("### :orange[Incident Summary]")
    col4.write("Select an incident to process by clicking the row")
    
    event = col4.dataframe(
        df,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        column_config={
            "incidentType": "Incident Type",
            "pk": "Session ID",
            "incidentIdentifier": "Database Instance",
            "incident_status": "Status",
            "incident_time": "Incident Time"
        },
        column_order=("pk", "incidentIdentifier", "incidentType", "incident_status", "incident_time")
    )
    
    # User actions
    col5.markdown("### :orange[User Action]")
    col5.write("Actions requiring manual intervention")
    
    runbook_action = col5.button("Analyze Incident", use_container_width=True)
    remediate_action = col5.button("Remediate Incident", use_container_width=True)
    
    col5.divider()
    
    # Handle selection
    rows = event['selection']['rows']
    selected_incident = None
    
    if len(rows) != 0:
        selected_incident = df.iloc[rows[0]]
        col4.info(f"Selected: {selected_incident['incident_id']}")
        
        st.session_state.selected_incident_context = f"Incident {selected_incident['incident_id']} ({selected_incident['incidentType']}) on {selected_incident['incidentIdentifier']}"
    
    # Get Runbook action
    if runbook_action:
        if selected_incident is None:
            col4.error("Please select an incident to get the runbook")
        else:
            with col4.status("Mahavat Agent retrieving runbook... (Follow the logs in your terminal to see what the agent is doing in real-time)"):
                col4.markdown(f"***Runbook Instructions for {selected_incident['incident_id']}***")
                
                prompt = f"""Perform comprehensive IDR analysis for {selected_incident['incidentType']} incident on {selected_incident['incidentIdentifier']} in region {AWS_REGION}:

**MANDATORY: Use this EXACT formatting structure:**

### Comprehensive Analysis

#### Executive Summary
- **Root Cause:** [Primary cause]
- **Impact:** [Service impact]
- **Current Constraint:** [Limiting factors]
- **Health Status:** [Critical/Degraded/Warning]

#### Key Findings from Multi-Tool Analysis

##### AWS API Analysis
- **Cluster Status:** [Status from describe-db-clusters]
- **Configuration:** [ACU limits, IOPS limits, engine version]
- **Resource Utilization:** [Current metrics]

##### Performance Insights Results
- **Metrics Status:** [PI enabled/disabled]
- **Top Wait Events:** [If available]
- **SQL Performance:** [If available]

##### PostgreSQL Diagnostics (via RDS Data API)
- **Problematic Query:** [From pg_stat_statements]
- **Query Cost:** [Analysis of expensive queries]
- **Active PIDs:** [From pg_stat_activity]
- **Connection Count:** [Active sessions]

##### CloudWatch Analysis
- **ACU Utilization:** [Peak usage and trends]
- **IOPS Utilization:** [Peak usage and trends]
- **CPU Metrics:** [CPU patterns]
- **Log Insights:** [Relevant findings]

#### Recommendations
[Specific remediation steps]

**EXECUTE THESE SPECIFIC TOOL CALLS IN ORDER:**

1. **Runbook Retrieval** (FIRST - Display prominently):
   - QueryKnowledgeBases: Get detailed runbook for the incident remediation from Main KB (ID: {MAIN_KB_ID})
   - Format runbook content with clear headers and steps for UI display
   - Show runbook content at the top of the analysis

2. **AWS API MCP** - Get cluster configuration and execute database queries:
   - call_aws: describe-db-clusters for {selected_incident['incidentIdentifier']}
   - call_aws: list-secrets to find secret ARN for target cluster
   - call_aws: rds-data execute-statement with pg_stat_statements query on target cluster
   - call_aws: rds-data execute-statement with pg_stat_activity query on target cluster
   - call_aws: rds-data execute-statement with pg_locks query on target cluster

3. **Performance Insights** - Call pi_mcp_server tools:
   - get_performance_insights_metrics(cluster_identifier="{selected_incident['incidentIdentifier']}")
   - get_top_sql_statements(cluster_identifier="{selected_incident['incidentIdentifier']}")
   - get_wait_events(cluster_identifier="{selected_incident['incidentIdentifier']}")

4. **CloudWatch Analysis**:
   - call_aws: cloudwatch get-metric-statistics for ACU utilization on target cluster
   - call_aws: cloudwatch get-metric-statistics for IOPS utilization on target cluster
   - describe_log_groups for {selected_incident['incidentIdentifier']}
   - execute_log_insights_query on correct log group

**DO NOT USE:**
- PostgreSQL MCP server (connects to wrong database)
- postgres_query_provider workflows (not needed for IDR runbook analysis)

**IMPORTANT:** Start with runbook display, then provide comprehensive analysis using AWS API + RDS Data API + Performance Insights + CloudWatch. Do NOT execute remediation actions."""
                
                response = st.session_state.unified_mahavat_agent(prompt)
                col4.markdown(str(response))
    
    # Remediate action
    if remediate_action:
        if selected_incident is None:
            col4.error("Please select an incident to auto-remediate")
        else:
            with col4.status("Mahavat Agent remediating incident... (Follow the logs in your terminal to see what the agent is doing in real-time)"):
                col4.markdown(f"***Auto-remediation for {selected_incident['incident_id']}***")
                
                prompt = f"""Remediate this {selected_incident['incidentType']} incident on {selected_incident['incidentIdentifier']} in region {AWS_REGION}. 

**MANDATORY: Use this EXACT formatting structure for remediation summary:**

### Incident Remediation Summary

#### Actions Completed
- ✅ [Action 1 with specific details and results]
- ✅ [Action 2 with specific details and results]
- ✅ [Action 3 with specific details and results]

#### Incident Details
- **Incident ID:** {selected_incident['incident_id']}
- **Status:** [RESOLVED/IN_PROGRESS/FAILED]
- **Completion Time:** [Timestamp]

#### Relevant Details
- **Cluster Name:** {selected_incident['incidentIdentifier']}
- **Changes Made:** [Specific modifications]
- **Verification Status:** [Post-remediation checks]

**IDR Remediation Only:**
- Use IDR incident specialist for remediation
- Execute the remediation steps to resolve the incident
- Update incident status when complete
- DO NOT call PostgreSQL diagnostic specialist after remediation
- DO NOT provide additional technical analysis after remediation is complete

**Focus:** Complete the remediation and stop. This is an IDR incident, not a PostgreSQL diagnostic request."""
                
                response = st.session_state.unified_mahavat_agent(prompt)
                col4.markdown(str(response))
                
                col4.success("✅ Remediation completed! Click 'Refresh' to see updated incident status.")
                if col4.button("Refresh Incidents", use_container_width=True):
                    st.rerun()

def show_all_incidents():
    """Show all incidents page"""
    st.title(":orange[All Incidents]")
    st.subheader(f":orange[Incident History as of] :blue[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]", divider=True)
    
    incidents = get_incidents_data(status=None)
    
    if not incidents:
        st.info("No incidents found")
        return
    
    # Prepare dataframe
    incidents_data = []
    for item in incidents:
        incidents_data.append({
            'incident_id': item.get('incident_id', ''),
            'incidentIdentifier': item.get('incidentIdentifier', item.get('incident_identifier', '')),
            'incidentType': item.get('incidentType', item.get('incident_type', '')),
            'incident_status': item.get('incident_status', ''),
            'incident_time': item.get('incident_time', ''),
            'alarm_name': item.get('alarm_name', ''),
            'created_at': item.get('created_at', ''),
            'runbook_used': item.get('resolution', ''),
            'remediation_steps': ', '.join(item.get('remediation_steps', []))
        })
    
    df = pd.DataFrame(incidents_data)
    df = df.sort_values('incident_time', ascending=False)
    
    st.markdown("### :orange[All Incidents]")
    st.dataframe(
        df,
        hide_index=True,
        column_config={
            "incident_id": "Incident ID",
            "incidentIdentifier": "Database Instance",
            "incidentType": "Type",
            "incident_status": "Status",
            "incident_time": "Incident Time",
            "alarm_name": "Alarm Name",
            "created_at": "Created At",
            "runbook_used": "Runbook Used"
            #"remediation_steps": "Remediation Steps"
        },
        column_order=("incident_id", "incidentIdentifier", "incidentType", "incident_status", "incident_time", "runbook_used")
    )
    
    st.caption(f"Total incidents: {len(df)}")

def main():
    """Main application"""
    st.set_page_config(page_title="Mahavat Agent v2 - Unified Database Management", layout="wide")
    
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)
    
    # Initialize authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Check authentication - show login page if not authenticated
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Initialize MCP clients (only after authentication)
    if 'mcp_clients' not in st.session_state:
        st.session_state.mcp_clients = create_available_mcp_clients()
    
    mcp_clients = st.session_state.mcp_clients
    
    # Initialize chat state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False
    if 'selected_incident_context' not in st.session_state:
        st.session_state.selected_incident_context = None
    
    # Sidebar
    with st.sidebar:
        st.image("Mahavat.png", width=120)
        st.subheader("Mahavat Agent v2")
        st.caption("Unified Database Management")
        st.caption("IDR + PostgreSQL Diagnostics")
        st.divider()
        
        # User info and logout
        if st.session_state.get('authenticated'):
            st.info(f"👤 **User:** {st.session_state.get('username', 'demo')}")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.clear()
                st.rerun()
            st.divider()
        
        page = st.radio("Navigation", ["Pending Incidents", "All Incidents"], key="page_nav")
        
        st.divider()
        
        # AWS-branded button styling with orange gradient
        st.markdown("""
            <style>
            div.stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #FF9900 0%, #EC7211 100%);
                color: white;
                border: none;
                font-weight: 600;
                box-shadow: 0 2px 4px rgba(255, 153, 0, 0.3);
            }
            div.stButton > button[kind="primary"]:hover {
                background: linear-gradient(135deg, #EC7211 0%, #FF9900 100%);
                box-shadow: 0 4px 6px rgba(255, 153, 0, 0.4);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Chat toggle in sidebar
        if st.button(
            "💬 Mahavat Agent v2 Chat",
            use_container_width=True,
            type="primary",
            help="Toggle the AI-powered chat interface",
            key="chat_toggle"
        ):
            st.session_state.show_chat = not st.session_state.show_chat
            st.rerun()
        
        st.divider()
        st.caption("Built with Strands Agents-as-Tools")
        
        # Custom CSS for MCP Server Status expander - lighter version of chat button
        st.markdown("""
            <style>
            /* Lighter version of chat button orange for MCP Server Status */
            div[data-testid="stExpander"] details summary {
                background: linear-gradient(135deg, rgba(255, 153, 0, 0.6) 0%, rgba(236, 114, 17, 0.6) 100%);
                color: white;
                font-weight: 600;
                border-radius: 4px;
                padding: 8px 12px;
                border: none;
            }
            div[data-testid="stExpander"] details summary:hover {
                background: linear-gradient(135deg, rgba(236, 114, 17, 0.6) 0%, rgba(255, 153, 0, 0.6) 100%);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # MCP Server Status - shows initialization messages here
        with st.expander("🛠️ MCP Server Status"):
            st.markdown("**Available MCP Servers:**")
            for server_name, client in mcp_clients.items():
                if client:
                    try:
                        tools = client.list_tools_sync()
                        st.success(f"✅ {server_name}: {len(tools)} tools available")
                    except:
                        st.warning(f"⚠️ {server_name}: Connected but tools unavailable")
                else:
                    st.error(f"❌ {server_name}: Not connected")
            st.caption(f"Total servers: {len(mcp_clients)}")
    
    # Initialize unified agent
    if 'unified_mahavat_agent' not in st.session_state:
        with st.spinner("🔧 Initializing Unified Mahavat Agent..."):
            st.session_state.unified_mahavat_agent = create_unified_mahavat_agent()
    
    # Main content
    if page == "Pending Incidents":
        show_pending_incidents()
    else:
        show_all_incidents()
    
    # Show chat section at bottom if enabled
    if st.session_state.show_chat:
        st.divider()
        
        # Chat header with controls in top-right corner
        chat_col1, chat_col2 = st.columns([4, 1])
        with chat_col1:
            st.markdown("### 💬 Mahavat Agent v2 Chat")
        with chat_col2:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🗑️", key="clear_chat", help="Clear chat history and context"):
                    st.session_state.chat_messages = []
                    st.session_state.selected_incident_context = None
                    st.success("Chat cleared!")
                    st.rerun()
            with btn_col2:
                if 'chat_expanded' not in st.session_state:
                    st.session_state.chat_expanded = False
                if st.button("⬆️" if not st.session_state.chat_expanded else "⬇️", 
                            key="toggle_chat_size", 
                            help="Expand or collapse chat area"):
                    st.session_state.chat_expanded = not st.session_state.chat_expanded
                    st.rerun()
        
        # Context indicator
        if st.session_state.selected_incident_context:
            st.info(f"🎯 Context: {st.session_state.selected_incident_context}")
        
        # Chat messages with dynamic height
        chat_height = 600 if st.session_state.get('chat_expanded', False) else 300
        chat_container = st.container(height=chat_height)
        with chat_container:
            for msg in st.session_state.chat_messages:
                avatar = "Mahavat.png" if msg["role"] == "assistant" else None
                with st.chat_message(msg["role"], avatar=avatar):
                    st.write(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about incidents, remediation, or PostgreSQL diagnostics...", key="chat_input"):
            handle_chat_message(prompt)

if __name__ == "__main__":
    main()
