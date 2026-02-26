#!/bin/bash
echo "🔧 DAT301 Workshop - System Setup"

# Update system
dnf update -y

# Fix curl conflicts
dnf remove -y curl-minimal || true

# Install basic packages
dnf install -y git wget unzip jq

# Skip Development Tools group install - it tries to remove protected packages
# Install only essential development packages individually
echo "📦 Installing essential development packages..."
dnf install -y gcc gcc-c++ make automake autoconf libtool || {
    echo "⚠️  Some development packages failed to install, continuing..."
}

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
ln -sf /usr/local/bin/aws /usr/bin/aws
rm -rf awscliv2.zip aws/

# Install Node.js
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
dnf install -y nodejs

# Install Amazon Q CLI
echo "📦 Installing Amazon Q CLI..."
curl -fsSL https://q.us-east-1.amazonaws.com/install.sh | bash
ln -sf /usr/local/bin/q /usr/bin/q || true

# Verify Q CLI installation
if command -v q &> /dev/null; then
    echo "✅ Q CLI installed: $(q --version 2>&1 | head -1)"
else
    echo "⚠️  Q CLI installation may have issues"
fi

echo "✅ System setup completed"