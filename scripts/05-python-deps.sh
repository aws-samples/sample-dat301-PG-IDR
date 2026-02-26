#!/bin/bash
echo "📦 DAT301 Workshop - Python Dependencies Setup"

# Install uv in participant's home directory
PARTICIPANT_HOME="/home/participant"

if [ ! -f "$PARTICIPANT_HOME/.local/bin/uv" ]; then
    export HOME="$PARTICIPANT_HOME"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ UV installed"
else
    echo "UV already installed"
fi

# Add UV to PATH in participant's bashrc
if ! grep -q ".local/bin" "$PARTICIPANT_HOME/.bashrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PARTICIPANT_HOME/.bashrc"
    echo "✅ Added UV to PATH"
fi

# Set up Python virtual environment in /workshop
cd /workshop

# Load pyenv environment
export PYENV_ROOT="$PARTICIPANT_HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

echo "Using Python: $(python --version)"
echo "Python path: $(which python)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    python -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install streamlit boto3 psycopg2-binary pydantic fastapi uvicorn python-jose[cryptography] loguru httpx python-multipart pandas plotly mcp

echo "✅ Python dependencies installed"

# Fix ownership
chown -R participant:participant "$PARTICIPANT_HOME/.local" "$PARTICIPANT_HOME/.bashrc" /workshop/.venv

echo "✅ Python dependencies setup completed"