# DAT301 - AI Powered PostgreSQL: Incident Detection & MCP Integration

<div align="center">

### Platform & Infrastructure
[![AWS Aurora](https://img.shields.io/badge/Aurora_PostgreSQL-17.x_Serverless_v2-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/rds/aurora/)
[![pgvector](https://img.shields.io/badge/pgvector-Vector_Store-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Bedrock](https://img.shields.io/badge/Amazon_Bedrock-Claude_Sonnet_4-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/)

### Languages & Frameworks
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-00ADD8?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI_Framework-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

[![License](https://img.shields.io/badge/License-MIT--0-green?style=for-the-badge)](LICENSE)

</div>

> 🎓 **AWS re:Invent 2025 Workshop** | 300-Level Expert Session

## 🚀 Overview

**Duration**: 120 minutes | **Level**: 300 - Expert

Discover how to leverage generative AI to transform PostgreSQL database management through an integrated solution combining incident detection and response (IDR) with the Model Context Protocol (MCP) for performance optimization. Build a comprehensive system utilizing Amazon Aurora PostgreSQL-Compatible Edition with pgvector that creates a robust vector store from diverse data sources including database documentation, runbooks, and incident records.

**What You'll Build:**
- AI-powered incident detection and response system with Mahavat Agent
- MCP-based agents for database performance optimization
- Vector-enabled knowledge base with runbooks and documentation
- Intelligent remediation recommendations using generative AI
- Real-time performance monitoring and automated scaling

## 🏗️ Workshop Architecture

### Complete Infrastructure Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Workshop Studio Environment              │
├─────────────────────────────────────────────────────────────────┤
│  VS Code IDE (Code Editor)                                     │
│  ├── Mahavat Agent V1 (IDR)     ├── Mahavat Agent V2 (Unified) │
│  ├── MCP Servers (Local STDIO)  ├── Streamlit UI               │
│  └── Workshop Repository        └── Load Testing Tools         │
├─────────────────────────────────────────────────────────────────┤
│  Authentication & Security                                      │
│  ├── AWS Cognito (User Pool)    ├── IAM Roles & Policies       │
│  └── Admin/Readonly Users       └── Workshop Studio Integration │
├─────────────────────────────────────────────────────────────────┤
│  Database Infrastructure                                        │
│  ├── Main Aurora PostgreSQL 17.x (pgvector enabled)            │
│  ├── IDR Aurora Serverless v2 (ACU scaling tests)              │
│  ├── IDR Provisioned Instance (IOPS testing)                   │
│  └── DynamoDB (Incident tracking)                              │
├─────────────────────────────────────────────────────────────────┤
│  AI & Knowledge Management                                      │
│  ├── Amazon Bedrock (Claude Sonnet 4, Titan Embed)             │
│  ├── Knowledge Base (S3 + pgvector)                            │
│  └── Vector Store (Runbooks, Documentation)                    │
├─────────────────────────────────────────────────────────────────┤
│  Monitoring & Observability                                     │
│  ├── CloudWatch Alarms & Metrics                               │
│  ├── Performance Insights                                       │
│  └── Automated Incident Creation                               │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Repository Structure

```
├── mahavat_agent/
│   ├── mahavat_agent_v1.py              # IDR Agent - Incident Detection & Response
│   ├── mahavat_agent_v2.py              # Unified Agent with MCP integration
│   ├── pi_mcp_server.py                 # Performance Insights MCP server
│   ├── idr_mcp_server.py                # IDR MCP server
│   ├── postgres_query_provider.py       # PostgreSQL query provider
│   └── requirements.txt                 # Python dependencies
├── database-workload/
│   ├── simulation-2.py                  # Database workload simulation
│   └── simulation-3.py                  # Advanced workload patterns
├── load-test/
│   ├── stress_test.py                   # Database stress testing
│   ├── acu-test.sh                      # ACU scaling tests
│   └── iops-test.sh                     # IOPS performance tests
├── runbooks/
│   ├── acu_remediation.md               # Aurora Serverless ACU remediation
│   └── iops_remediation.md              # IOPS optimization runbook
└── scripts/
    ├── workshop-setup-complete-dynamic.sh  # Complete workshop setup
    ├── validate-environment.sh          # Environment validation
    └── database/                        # Database setup scripts
        ├── 01-extensions.sql
        ├── 02-roles.sql
        └── 03-tables.sql
```

## 🎯 Workshop Modules

### Prerequisites (10 minutes)
- Access Workshop Studio environment
- Verify VS Code IDE access
- Validate infrastructure deployment

### Module 1: Incident Detection & Response with Mahavat Agent V1 (40 minutes)

**Hands-On Activities:**
1. **Start IDR Agent** - Launch Mahavat Agent V1 with Streamlit UI
2. **Configure CloudWatch Alarms** - Set up IOPS monitoring and incident triggers
3. **Create Knowledge Base** - Deploy Bedrock Knowledge Base with vector storage
4. **Add Runbooks** - Upload and sync remediation runbooks to vector store
5. **Simulate IOPS Incident** - Trigger performance issues and observe detection
6. **Get Runbook Recommendations** - Experience AI-powered runbook retrieval
7. **Remediate IOPS Incident** - Follow AI recommendations to resolve issues

**Key Learning:**
- Vector similarity search for incident matching
- Automated runbook recommendations using pgvector
- Integration with DynamoDB for incident tracking
- CloudWatch alarm integration with Lambda triggers

### Module 2: Advanced MCP Integration with Mahavat Agent V2 (50 minutes)

**Hands-On Activities:**
1. **Start Unified Agent** - Launch Mahavat Agent V2 with MCP integration
2. **Configure ACU Alarms** - Set up Aurora Serverless v2 scaling monitoring
3. **Upload ACU Runbooks** - Add serverless-specific remediation guides
4. **Simulate ACU Incident** - Trigger capacity scaling scenarios
5. **Experience MCP Queries** - Natural language database performance queries
6. **Remediate ACU Incident** - Use MCP-powered recommendations
7. **Performance Analysis** - Deep dive into Performance Insights data

**Key Learning:**
- Model Context Protocol implementation for database management
- Aurora Serverless v2 ACU scaling patterns
- Performance Insights integration through MCP
- Natural language to SQL translation with Claude Sonnet 4

### Bonus Module: Understanding Agent Architecture (20 minutes)

**Deep Dive:**
- Agent code walkthrough and architecture patterns
- MCP server implementation details
- Vector store optimization techniques
- Customization strategies for production use

## 🛠️ Getting Started

### Workshop Studio Access

This workshop is delivered through **AWS Workshop Studio** - no personal AWS account required!

1. **Access Workshop Portal** - Use provided Workshop Studio URL
2. **Login** - Use your registration credentials
3. **Launch Environment** - Click "Open VS Code IDE"
4. **Verify Setup** - All infrastructure is pre-deployed

### Environment Validation

```bash
# Validate workshop environment
./scripts/validate-environment.sh
```

### Launch Mahavat Agents

**IDR Agent (Module 1):**
```bash
cd mahavat_agent
./mahavat_agent_v1.sh
```

**Unified Agent (Module 2):**
```bash
cd mahavat_agent
./mahavat_agent_v2.sh
```

## 🤖 AI-Powered Features

### Mahavat Agent V1 - Incident Detection & Response
- **Vector Similarity Search**: Match incidents to historical patterns using pgvector
- **Automated Runbook Retrieval**: AI-powered remediation guide recommendations
- **Context-Aware Responses**: Leverage database state and CloudWatch metrics
- **DynamoDB Integration**: Track incident lifecycle and resolution status

### Mahavat Agent V2 - MCP-Enhanced Performance Optimization
- **Natural Language Queries**: "Show me slow queries from the last hour"
- **Performance Insights Integration**: Direct access to PI data through MCP
- **Intelligent Analysis**: AI-powered performance bottleneck identification
- **Proactive Recommendations**: Prevent issues before they impact users

### Knowledge Management System
- **Vector Store**: Searchable documentation and runbooks using pgvector
- **Continuous Learning**: Improve responses from incident history
- **Multi-Modal Context**: Combine metrics, logs, and documentation
- **Bedrock Integration**: Titan embeddings for semantic search

## 🔧 AWS Services Architecture

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Amazon Aurora PostgreSQL 17.x** | Primary database with pgvector extension | r7g.xlarge, Multi-AZ |
| **Aurora Serverless v2** | ACU scaling demonstration | 0.5-16 ACU range |
| **Aurora Provisioned** | IOPS testing and optimization | gp3 storage, configurable IOPS |
| **Amazon Bedrock** | Claude Sonnet 4, Titan Embed v2 | us-west-2 region |
| **Amazon DynamoDB** | Incident tracking and state management | On-demand billing |
| **AWS Cognito** | User authentication (admin/readonly) | User pool with 2 users |
| **Amazon CloudWatch** | Performance metrics and alarming | Custom metrics, Lambda triggers |
| **AWS Performance Insights** | Database performance analysis | 7-day retention |
| **Amazon S3** | Knowledge base document storage | Versioned bucket |
| **AWS Lambda** | Incident creation automation | Python 3.9 runtime |

## 📊 Performance Testing & Monitoring

### Load Testing Tools

```bash
# Aurora Serverless ACU scaling test
./load-test/acu-test.sh

# IOPS performance and scaling test  
./load-test/iops-test.sh

# Comprehensive database stress test
python load-test/stress_test.py
```

### Database Workload Simulation

```bash
# Basic workload patterns
python database-workload/simulation-2.py

# Advanced performance scenarios
python database-workload/simulation-3.py
```

### Real-time Monitoring

- **CloudWatch Dashboards**: Pre-configured performance dashboards
- **Performance Insights**: Query-level performance analysis
- **Custom Metrics**: Application-specific monitoring
- **Automated Alerting**: Lambda-triggered incident creation

## 🎯 Key Takeaways

### When to Use AI-Powered IDR
- **Complex Multi-System Failures**: Incidents requiring contextual analysis
- **Knowledge Retention**: Preserve tribal knowledge in searchable vector stores
- **Rapid Response**: Reduce MTTR with automated runbook retrieval
- **Pattern Recognition**: Learn from historical incident data
- **Continuous Improvement**: Evolve responses based on outcomes

### MCP Benefits for Database Management
- **Structured Queries**: Natural language to SQL translation with context
- **Dynamic Tool Selection**: Choose appropriate data sources per query intent
- **Context Preservation**: Maintain conversation state across multiple tools
- **Security Integration**: Row-level security with persona-based access
- **Real-time Analysis**: Direct access to live performance data

### Production Considerations
- **Vector Index Optimization**: HNSW indexes for large-scale similarity search
- **Caching Strategy**: Redis for frequently accessed runbooks and queries
- **Monitoring Integration**: Custom CloudWatch metrics for agent performance
- **Security**: IAM roles, Cognito integration, and data encryption
- **Scalability**: Aurora Serverless v2 for variable workloads

## 🚀 Next Steps

### Extend This Workshop
1. **Custom Runbooks**: Add domain-specific remediation procedures
2. **Integration**: Connect with existing monitoring and ticketing systems
3. **Custom MCP Servers**: Build specialized tools for your environment
4. **Advanced Analytics**: Implement predictive incident detection

## 📚 Resources

### Core Technologies
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standardized AI tool protocol
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search for PostgreSQL
- [Aurora PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/) - Managed PostgreSQL database
- [Strands Agent Framework](https://strandsagents.com/) - MCP-compatible agent development

### AWS Documentation
- [Amazon Bedrock](https://aws.amazon.com/bedrock/) - Claude Sonnet 4 and Titan models
- [Performance Insights](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/USER_PerfInsights.html) - Database performance monitoring
- [Aurora Serverless v2](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html) - Auto-scaling database
- [Workshop Studio](https://workshops.aws/) - AWS workshop platform

### Workshop Materials
- **GitHub Repository**: [riv25-dat301](https://github.com/rameshv29/riv25-dat301) (reInvent-2025 branch)
- **Workshop Guide**: Available in VS Code IDE environment
- **Sample Data**: Pre-loaded incident scenarios and runbooks

## 🤝 Contributing

This workshop is maintained by AWS and the community. For issues, improvements, or questions:

- 🐛 Report issues through Workshop Studio feedback
- 💡 Suggest improvements via workshop evaluation
- ⭐ Star the repository for updates
- 🍴 Fork for your own customizations

## 📄 License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

---

<div align="center">

**AWS re:Invent 2025 | DAT301 - 300 Level Expert Session**

*AI powered PostgreSQL: Incident detection & MCP integration*

**Workshop Authors**: Ramesh Kumar Venkatraman, Chirag Dave

</div>
