#!/bin/bash
echo "💻 DAT301 Workshop - Code Server Setup"

# Install code-server
export HOME=/root
curl -fsSL https://code-server.dev/install.sh | bash

# Verify installation
if [ ! -f /usr/bin/code-server ]; then
    echo "Code-server installation failed, trying alternative method..."
    curl -fL https://github.com/coder/code-server/releases/download/v4.105.0/code-server-4.105.0-amd64.rpm -o /tmp/code-server.rpm
    rpm -i /tmp/code-server.rpm
fi

# Configure code-server for participant user (DAT409 security pattern)
mkdir -p /home/participant/.config/code-server
cat > /home/participant/.config/code-server/config.yaml << EOF
bind-addr: 127.0.0.1:8080
auth: password
password: ${CODE_EDITOR_PASSWORD:-TempPass123!}
cert: false
disable-telemetry: true
disable-update-check: true
disable-workspace-trust: true
disable-file-downloads: false
EOF

# Create VS Code user settings
mkdir -p /home/participant/.local/share/code-server/User
cat > /home/participant/.local/share/code-server/User/settings.json << 'EOF'
{
  "workbench.startupEditor": "none",
  "terminal.integrated.enablePersistentSessions": false,
  "terminal.integrated.confirmOnExit": "never",
  "terminal.integrated.copyOnSelection": true,
  "terminal.integrated.rightClickBehavior": "paste",
  "security.workspace.trust.enabled": false,
  "files.autoSave": "afterDelay"
}
EOF

# Create workspace file to open /workshop folder by default
cat > /home/participant/workshop.code-workspace << 'EOF'
{
  "folders": [
    {
      "path": "/workshop"
    }
  ],
  "settings": {}
}
EOF

# Create systemd TEMPLATE service for code-server (DAT409 security pattern)
cat > /etc/systemd/system/code-server@.service << 'EOF'
[Unit]
Description=code-server for %i
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=/workshop
Environment="HOME=/home/%i"
ExecStart=/bin/bash -c 'export PYENV_ROOT="$HOME/.pyenv" && export PATH="$PYENV_ROOT/bin:$HOME/.local/bin:$PATH" && eval "$(pyenv init -)" && /usr/bin/code-server --bind-addr 127.0.0.1:8080 --auth password /workshop'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set ownership
chown -R participant:participant /home/participant/

echo "✅ Code Server setup completed (localhost binding, participant user)"