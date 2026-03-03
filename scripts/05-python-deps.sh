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

# Make uv available for this script
export PATH="$PARTICIPANT_HOME/.local/bin:$PATH"

# Set up Python virtual environment in /workshop
cd /workshop

# Use uv to create venv (it downloads python automatically, no pyenv needed)
if [ ! -d ".venv" ]; then
    uv venv .venv --python 3.12
    echo "✅ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Install dependencies using uv (much faster than pip)
uv pip install --python .venv/bin/python streamlit boto3 psycopg2-binary pydantic fastapi uvicorn "python-jose[cryptography]" loguru httpx python-multipart pandas plotly mcp

echo "✅ Python dependencies installed"

# Fix ownership
chown -R participant:participant "$PARTICIPANT_HOME/.local" "$PARTICIPANT_HOME/.bashrc"
chown -R participant:participant "$PARTICIPANT_HOME/.cache" 2>/dev/null || true
chown -R participant:participant /workshop/.venv

echo "✅ Python dependencies setup completed"
