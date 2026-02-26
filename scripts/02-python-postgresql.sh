#!/bin/bash
echo "🐍 DAT301 Workshop - Python 3.11.13 + PostgreSQL Setup"

# IMPORTANT: Keep system Python (3.9) untouched for dnf/yum
echo "📋 System Python will remain: $(python3 --version)"

# Install build dependencies
dnf install -y \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    readline-devel \
    sqlite-devel \
    ncurses-devel \
    xz-devel \
    tk-devel \
    gdbm-devel \
    libuuid-devel \
    expat-devel

# Install PostgreSQL 17
dnf install -y postgresql17-server postgresql17 postgresql17-server-devel postgresql17-contrib

# Create workshop directory first
mkdir -p /workshop
chown participant:participant /workshop

# Install pyenv in participant's home directory
PARTICIPANT_HOME="/home/participant"
cd "$PARTICIPANT_HOME"

# Install pyenv
if [ ! -d "$PARTICIPANT_HOME/.pyenv" ]; then
    export HOME="$PARTICIPANT_HOME"
    curl https://pyenv.run | bash
fi

# Configure pyenv in participant's bashrc (avoid duplicates)
if ! grep -q "PYENV_ROOT" "$PARTICIPANT_HOME/.bashrc"; then
    cat >> "$PARTICIPANT_HOME/.bashrc" << 'PYENV_EOF'
# Pyenv configuration (user-only, does not affect system Python)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
PYENV_EOF
fi

# Load pyenv for current session
export PYENV_ROOT="$PARTICIPANT_HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Install Python 3.11.13
pyenv install 3.11.13 || echo "Python 3.11.13 already installed"

# Set local Python version for workshop directory
cd /workshop
pyenv local 3.11.13

# Fix ownership
chown -R participant:participant "$PARTICIPANT_HOME/.pyenv" /workshop/.python-version

echo "✅ Python 3.11.13 installed for participant user"

# Verify system Python is still intact
echo "🔍 Verification:"
echo "System Python: $(/usr/bin/python3 --version)"
echo "DNF status: $(dnf --version | head -1)"

echo "✅ Python 3.11.13 and PostgreSQL setup completed"