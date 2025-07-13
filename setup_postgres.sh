#!/bin/bash

echo "PostgreSQL Setup for LPE with Embeddings"
echo "========================================"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL not found. Installing with Homebrew..."
    brew install postgresql
    brew services start postgresql
else
    echo "✅ PostgreSQL found"
fi

# Install Python requirements
echo "Installing Python dependencies..."
pip3 install --user asyncpg psycopg2-binary

# Create database and user
echo "Setting up database..."
createdb lamish_projection_engine 2>/dev/null || echo "Database may already exist"

psql -d lamish_projection_engine -c "
CREATE USER lpe_user WITH PASSWORD 'lpe_password';
GRANT ALL PRIVILEGES ON DATABASE lamish_projection_engine TO lpe_user;
CREATE EXTENSION IF NOT EXISTS vector;
" 2>/dev/null || echo "Database setup may already be complete"

# Set environment variables
echo "Setting up environment..."
echo "export LPE_USE_POSTGRES=true" >> ~/.zshrc
echo "export LPE_POSTGRES_USER=lpe_user" >> ~/.zshrc  
echo "export LPE_POSTGRES_PASSWORD=lpe_password" >> ~/.zshrc
echo "export LPE_POSTGRES_DB=lamish_projection_engine" >> ~/.zshrc

echo ""
echo "✅ PostgreSQL setup complete!"
echo "Restart your terminal or run: source ~/.zshrc"
echo "Then restart the LPE interfaces to use PostgreSQL with embeddings."
echo ""
echo "Note: You may need to install pgvector extension separately:"
echo "git clone https://github.com/pgvector/pgvector.git"
echo "cd pgvector && make && make install"