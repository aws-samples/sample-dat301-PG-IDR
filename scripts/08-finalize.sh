#!/bin/bash
echo "🎉 DAT301 Workshop - Finalization"

# Create workshop README
cat > /workshop/WORKSHOP_README.md << 'EOF'
# DAT301 re:Invent 2025 Workshop

## AI-Powered PostgreSQL with Local MCP Servers

### Quick Start

1. **Access VS Code**: Already running on port 8080

### Authentication

- **Admin User**: `workshop_admin` / `AdminPass2025!` (full database access)
- **Readonly User**: `workshop_readonly` / `ReadonlyPass2025!` (catalog access only)

### Mahavat Agent

The **mahavat-agent** has been automatically downloaded and extracted to `/workshop/mahavat-agent/`.
This agent provides additional AI-powered database analysis capabilities for the workshop.

### Workshop Scenarios

1. **Slow Query Analysis**: Identify and optimize performance issues
2. **Connection Troubleshooting**: Diagnose connection problems
3. **Capacity Planning**: Analyze growth trends and scaling needs
4. **Vector Search**: Explore pgvector capabilities

### Environment Variables

All configuration is in `/workshop/.env` file.

### Database Setup

Run `./setup_database.sh` to create database roles and sample data.
EOF

# Start services
systemctl daemon-reload
systemctl enable code-server
systemctl start code-server

# Final ownership fix
chown -R ec2-user:ec2-user /workshop/
chown -R ec2-user:ec2-user /home/ec2-user/

echo "🎉 Workshop setup completed successfully!"
echo "📋 Services Status:"
systemctl is-active code-server && echo "✅ Code Server: Running" || echo "❌ Code Server: Failed"
echo "📁 Workshop directory: /workshop"
echo "🌐 Access via CloudFront URL"