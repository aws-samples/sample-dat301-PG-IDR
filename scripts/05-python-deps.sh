#!/bin/bash
echo "📦 DAT301 Workshop - Python Dependencies Setup"

# Install uv for participant user
su - participant -c 'bash -s' << 'EOF'
if [ ! -f "$HOME/.local/bin/uv" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ UV installed"
else
    echo "UV already installed"
fi

# Add UV to PATH if not already there
if ! grep -q ".local/bin" ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "✅ Added UV to PATH"
fi
EOF

# Set up Python virtual environment as participant user
su - participant -c 'bash -s' << 'EOF'
cd /workshop

# Load pyenv environment
export PYENV_ROOT="$HOME/.pyenv"
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
EOF

echo "✅ Python dependencies setup completed"