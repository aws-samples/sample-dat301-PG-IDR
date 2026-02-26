#!/bin/bash
echo "📦 DAT301 Workshop - Python Dependencies Setup (Safe Mode)"

# Install uv for participant (not root)
sudo -u participant bash << 'EOF'
cd /home/participant
if [ ! -f "$HOME/.local/bin/uv" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "UV already installed"
fi

# Add UV to PATH if not already there
if ! grep -q ".local/bin" ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "✅ Added UV to PATH in .bashrc"
fi
EOF

# Set up Python environment as participant
sudo -u participant bash << 'EOF'
cd /workshop

# Load pyenv environment
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Verify we're using the right Python
echo "Using Python: $(python --version)"
echo "Python path: $(which python)"

# Create virtual environment with pyenv Python 3.11.13
if [ ! -d ".venv" ]; then
    python -m venv .venv
else
    echo "Virtual environment already exists"
fi

source .venv/bin/activate

# Verify virtual environment
echo "Venv Python: $(python --version)"
echo "Venv pip: $(which pip)"

# Install core dependencies
pip install --upgrade pip
pip install streamlit boto3 psycopg2-binary pydantic fastapi uvicorn python-jose[cryptography] loguru httpx python-multipart pandas plotly mcp

echo "✅ Virtual environment created with Python 3.11.13"
EOF

echo "✅ Python dependencies setup completed safely"