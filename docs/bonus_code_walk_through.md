---
title: "Bonus: Understanding the Mahavat Agents"
chapter: false
weight: 90
---

:::alert{type="success"}
**🎉 Congratulations!** You've successfully used both Mahavat Agent V1 and V2. Now let's peek under the hood to understand how they actually work.
:::

## What You'll Learn

**Duration:** 20 minutes  
**Format:** Interactive code walkthrough

By the end of this module, you'll understand:
- ✅ How the agents you just used actually work
- ✅ The key differences between V1 and V2 architectures
- ✅ Why certain design decisions were made
- ✅ How to customize the agents for your needs

---

::::expand{header="🔍 What You Just Experienced (5 minutes)"}

### Mahavat Agent V1 (IDR Agent)

**What You Did:**
- Investigated incidents like "INC-001"
- Asked questions like "What's the status of this incident?"
- Saw the agent retrieve runbooks and suggest remediation

**What Happened Behind the Scenes:**
```
Your Query → Streamlit UI → IDR Agent
                              ↓
                    ┌─────────┼─────────┐
                    ↓         ↓         ↓
                IDR MCP   KB MCP   AWS API
                Server    Server   MCP Server
                    ↓         ↓         ↓
                DynamoDB  Bedrock  AWS APIs
                          KB
```

**Architecture:** Single-purpose agent with 3 MCP servers  
**Code Location:** `mahavat_agent/mahavat_agent_v1.py` (~700 lines)

---

### Mahavat Agent V2 (Unified Agent)

**What You Did:**
- Asked PostgreSQL questions like "Why is my query slow?"
- Investigated incidents with natural language
- Saw the agent route to appropriate specialists

**What Happened Behind the Scenes:**
```
Your Query → Streamlit UI → Router Agent
                              ↓
                    ┌─────────┼─────────┐
                    ↓                   ↓
            PostgreSQL              IDR
            Specialist              Specialist
            Agent                   Agent
                    ↓                   ↓
            7 MCP Servers          3 MCP Servers
```

**Architecture:** Router + Specialists with 8 MCP servers  
**Code Location:** `mahavat_agent/mahavat_agent_v2.py` (~1300 lines)

:::alert{type="info"}
**Try This:** Open both files in VS Code and compare their structure. Notice how V2 is significantly more complex but also more powerful.
:::

::::

::::expand{header="🏗️ Architecture Deep Dive (8 minutes)"}

### The Magic: MCP Server Initialization

When you saw this in the terminal:
```
🔧 Initializing IDR Agent...
✅ idr: 5 tools
✅ main_kb: 2 tools
✅ aws_api: 8 tools
```

**What's happening in the code:**

**File:** `mahavat_agent_v1.py`, **Lines:** 200-280

```python
# MCP server configurations
mcp_configs = {
    'idr': {
        'params': StdioServerParameters(
            command="python3",
            args=[os.path.join(os.path.dirname(__file__), "idr_mcp_server.py")],
            env={"AWS_REGION": AWS_REGION, "DYNAMODB_TABLE": DYNAMODB_TABLE}
        ),
        'required': True,
        'description': 'Incident management'
    },
    'main_kb': {
        'params': StdioServerParameters(
            command="uvx",
            args=["awslabs.bedrock-kb-retrieval-mcp-server@latest"],
            env={"AWS_REGION": AWS_REGION, "KNOWLEDGE_BASE_ID": MAIN_KB_ID}
        ),
        'required': True,
        'description': 'Knowledge base retrieval'
    }
}
```

**Key Insights:**
- **STDIO Protocol:** Servers communicate via stdin/stdout (no network overhead)
- **Custom Server:** `idr_mcp_server.py` is our own Python server for DynamoDB
- **AWS Servers:** `bedrock-kb-retrieval` is pre-built by AWS
- **Environment Variables:** Each server gets the config it needs

:::alert{type="info"}
**Try This:** Look at `mahavat_agent/idr_mcp_server.py` to see how we built a custom MCP server for incident management.
:::

---

### Tool Collection: The Agent's Toolkit

When you asked "Investigate INC-001", the agent knew exactly which tools to use.

**File:** `mahavat_agent_v1.py`, **Lines:** 285-320

```python
# Collect all available tools from MCP servers
all_mcp_tools = []
for server_name, client in mcp_clients.items():
    if client:
        tools = client.list_tools_sync()
        all_mcp_tools.extend(tools)

# Add custom utility tools
custom_tools = [current_time]

# Agent gets access to ALL tools
all_tools = all_mcp_tools + custom_tools
```

**What tools does the agent have?**

**From IDR MCP Server:**
- `get_incident_details(incident_id: str)`
- `update_incident_status(incident_id: str, status: str)`
- `list_pending_incidents()`
- `create_incident(...)`

**From Knowledge Base MCP Server:**
- `retrieve(query: str)` - Search runbooks
- `retrieve_and_generate(query: str)` - Search + summarize

**From AWS API MCP Server:**
- `call_aws(service: str, operation: str, parameters: dict)`
- Various AWS resource operations

**Total:** ~15 tools available to V1 agent

---

### System Prompt: The Agent's Instructions

The system prompt is like giving the agent a job description and training manual.

**File:** `mahavat_agent_v1.py`, **Lines:** 325-370

```python
idr_system_prompt = f"""You are an AWS incident analysis and remediation specialist.

**Your Role:**
- Analyze AWS infrastructure incidents
- Retrieve relevant runbooks from knowledge base
- Execute remediation steps
- Update incident status in DynamoDB

**Workflow:**
1. **Get Incident Details**: Use get_incident_details(incident_id)
2. **Search Knowledge Base**: Use retrieve(query) to find runbooks
3. **Analyze Issue**: Review incident data and runbook guidance
4. **Execute Remediation**: Use call_aws() for AWS operations
5. **Update Status**: Use update_incident_status() to track progress

**Important Guidelines:**
- Always retrieve runbooks before suggesting remediation
- Filter out rdsadmin schemas from PostgreSQL queries
- Provide clear explanations for all actions
"""
```

**Why this matters:**
- **Identity:** "You are an AWS incident specialist" - defines the agent's role
- **Workflow:** Step-by-step process guides behavior
- **Guidelines:** Rules prevent common mistakes

:::alert{type="warning"}
**Key Insight:** The system prompt is crucial - it's how you "train" the agent without actually training a model!
:::

::::

::::expand{header="🚀 V2's Innovation: Agent-as-Tools (5 minutes)"}

### The Game Changer: Specialists as Tools

V2's breakthrough is treating entire agents as tools that can be called by a router agent.

**File:** `mahavat_agent_v2.py`, **Lines:** 365-545

```python
@tool
def postgres_diagnostic_specialist(
    query: str, 
    context: str = "",
    enable_streaming: bool = True
) -> str:
    """PostgreSQL diagnostic specialist with available MCP servers.
    
    Use this specialist for:
    - PostgreSQL performance analysis
    - Query optimization
    - Database health checks
    """
    
    # Get PostgreSQL-specific tools only
    postgres_servers = [
        'postgres_query_provider',  # Query execution
        'performance_insights',     # RDS Performance Insights
        'cloudwatch',              # CloudWatch metrics
        'main_kb'                  # Knowledge base
    ]
    
    # Create specialist with focused expertise
    postgres_agent = Agent(
        model=BedrockModel(model_id=BEDROCK_MODEL_ID, region=AWS_REGION),
        tools=postgres_mcp_tools + standard_tools,
        system_prompt=postgres_system_prompt  # PostgreSQL-specific instructions
    )
    
    return str(postgres_agent(query))
```

**What makes this powerful:**
- **@tool Decorator:** Makes the specialist callable like any other tool
- **Specialized Tools:** Only loads PostgreSQL-relevant MCP servers (7 instead of 8)
- **Specialized Prompt:** PostgreSQL-specific instructions and workflow
- **Agent Inside Tool:** Creates a new agent instance with focused expertise

---

### The Router: Traffic Controller

**File:** `mahavat_agent_v2.py`, **Lines:** 760-900

```python
unified_system_prompt = f"""You are the Mahavat Agent - an intelligent router.

**Routing Decision Matrix:**

**Use postgres_diagnostic_specialist when:**
- Keywords: PostgreSQL, performance, slow queries, table bloat, VACUUM
- Performance analysis requests
- Database health checks

**Use idr_incident_specialist when:**
- Keywords: incidents, alarms, remediation, runbooks
- Incident management requests

**Use Direct MCP Tools when:**
- Simple information retrieval
- Single tool call sufficient
"""

# Router agent with specialists as tools
unified_agent = Agent(
    model=BedrockModel(model_id=BEDROCK_MODEL_ID, region=AWS_REGION),
    tools=[
        postgres_diagnostic_specialist,  # Specialist as tool
        idr_incident_specialist,         # Specialist as tool
        *all_mcp_tools,                  # All MCP tools directly
        *standard_tools                  # Standard utility tools
    ],
    system_prompt=unified_system_prompt
)
```

**Example: "Why is my query slow?"**

1. **Router analyzes:** Keywords "query slow" → PostgreSQL issue
2. **Router calls:** `postgres_diagnostic_specialist(query="Why is my query slow?")`
3. **Specialist executes:** Multiple PostgreSQL tools to diagnose
4. **Specialist returns:** Complete analysis with recommendations
5. **You see:** Comprehensive diagnostic report

:::alert{type="success"}
**Try This:** Ask V2 agent both PostgreSQL and incident questions to see how it routes differently.
:::

::::

::::expand{header="🎯 Design Decisions & When to Use Each (2 minutes)"}

### V1 vs V2: Architecture Comparison

| Aspect | V1 (Single Agent) | V2 (Router + Specialists) |
|--------|-------------------|---------------------------|
| **Lines of Code** | 700 | 1300 |
| **MCP Servers** | 3 | 8 |
| **Total Tools** | ~15 | ~50+ |
| **Agents** | 1 | 3 (Router + 2 Specialists) |
| **Complexity** | Low | Medium |
| **Scalability** | Limited | High |
| **Best For** | Single domain | Multiple domains |

### When to Choose Each Architecture

#### Choose V1 When:
- ✅ Single purpose application (just IDR)
- ✅ Less than 20 tools total
- ✅ Simple workflows
- ✅ Quick prototyping
- ✅ Team has limited AI/agent experience

#### Choose V2 When:
- ✅ Multiple domains (PostgreSQL + IDR + more)
- ✅ More than 20 tools
- ✅ Complex workflows requiring expertise
- ✅ Production applications
- ✅ Team collaboration (different specialists)
- ✅ Need to scale to new domains

:::alert{type="info"}
**Real-world tip:** Start with V1 architecture, then migrate to V2 when you need multiple domains or hit tool limits.
:::

::::

## 🛠️ Customization Examples

### Add a Custom Tool (V1 or V2)

**File:** `mahavat_agent_v1.py` or `mahavat_agent_v2.py`  
**Location:** After line 320 (custom tools section)

```python
@tool
def get_database_size() -> str:
    """Get the total size of the database in MB"""
    query = "SELECT pg_size_pretty(pg_database_size(current_database()))"
    # Implementation would use postgres_query_provider
    return f"Database size: {result}"

# Add to custom_tools list
custom_tools = [current_time, get_database_size]
```

### Add a New Specialist (V2 only)

```python
@tool
def security_specialist(query: str) -> str:
    """Security analysis specialist for compliance and vulnerability checks"""
    
    security_tools = []  # Get security-related MCP tools
    security_prompt = """You are a security specialist..."""
    
    security_agent = Agent(
        model=BedrockModel(...),
        tools=security_tools,
        system_prompt=security_prompt
    )
    
    return str(security_agent(query))
```

---

## 🎯 Key Takeaways

### What You Learned

✅ **MCP Integration:** How STDIO servers provide tools to agents  
✅ **Tool Collection:** How agents get access to multiple capabilities  
✅ **System Prompts:** How to guide agent behavior without training  
✅ **V1 Architecture:** Single agent for focused use cases  
✅ **V2 Architecture:** Router + Specialists for complex scenarios  
✅ **Customization:** How to add tools and specialists  

### Design Patterns You Can Reuse

1. **MCP Server Configuration:** Standardized way to connect external tools
2. **Tool Collection:** Gather capabilities from multiple sources
3. **Specialist as Tool:** Treat agents as callable functions
4. **Router Logic:** Let LLM decide which specialist to use
5. **System Prompt Engineering:** Guide behavior through instructions

---

## 🚀 Next Steps

### Immediate Actions
1. ✅ Explore the code files with your new understanding
2. ✅ Try modifying a system prompt to change behavior
3. ✅ Add a simple custom tool to see how it works

### Future Learning
1. 📚 Study the MCP specification at [modelcontextprotocol.io](https://modelcontextprotocol.io/)
2. 🔨 Build your own custom MCP server
3. 🚀 Deploy agents in your own environment
4. 🤝 Share your learnings with the community

### Resources
- **Code Repository:** All workshop code is in `mahavat_agent/` directory
- **Strands Framework:** [GitHub - strands-ai/strands](https://github.com/strands-agents/sdk-python)
- **MCP Protocol:** [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- **AWS Bedrock:** [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

:::alert{type="success"}
**🎉 Congratulations!** You now understand how to build production-ready AI agents with MCP integration. The patterns you've learned can be applied to any domain - from database management to security analysis to customer support.
:::

---

**Questions?** Ask in the workshop chat or reach out to the instructors.

*Workshop: DAT301 - AI powered PostgreSQL: Incident detection & MCP integration*
