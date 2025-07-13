#!/bin/bash
# Check Python installations and SSL support

echo "Checking Python installations..."
echo "================================"

# Check system Python3
echo -e "\n1. System Python3 (/usr/bin/python3):"
if [ -f /usr/bin/python3 ]; then
    /usr/bin/python3 --version
    /usr/bin/python3 -c "import ssl; print('  SSL module: OK')" 2>/dev/null || echo "  SSL module: NOT AVAILABLE"
else
    echo "  Not found"
fi

# Check Homebrew Python
echo -e "\n2. Homebrew Python (/usr/local/bin/python3):"
if [ -f /usr/local/bin/python3 ]; then
    /usr/local/bin/python3 --version
    /usr/local/bin/python3 -c "import ssl; print('  SSL module: OK')" 2>/dev/null || echo "  SSL module: NOT AVAILABLE"
else
    echo "  Not found"
fi

# Check Homebrew Python (Apple Silicon)
echo -e "\n3. Homebrew Python ARM64 (/opt/homebrew/bin/python3):"
if [ -f /opt/homebrew/bin/python3 ]; then
    /opt/homebrew/bin/python3 --version
    /opt/homebrew/bin/python3 -c "import ssl; print('  SSL module: OK')" 2>/dev/null || echo "  SSL module: NOT AVAILABLE"
else
    echo "  Not found"
fi

# Check current Python
echo -e "\n4. Current Python (python3):"
which python3
python3 --version
python3 -c "import ssl; print('  SSL module: OK')" 2>/dev/null || echo "  SSL module: NOT AVAILABLE"

# Check conda Python
echo -e "\n5. Conda Python:"
if command -v conda &> /dev/null; then
    conda info --envs
    python --version
    python -c "import ssl; print('  SSL module: OK')" 2>/dev/null || echo "  SSL module: NOT AVAILABLE"
else
    echo "  Conda not found"
fi

echo -e "\n================================"
echo "Recommendation:"
echo "Use a Python installation where 'SSL module: OK' is shown."