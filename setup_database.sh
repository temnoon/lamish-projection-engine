#!/bin/bash
# Setup PostgreSQL database for LPE

echo "🗄️ Setting up PostgreSQL database for LPE..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if PostgreSQL container exists
if docker ps -a | grep -q lpe-postgres; then
    echo "📦 PostgreSQL container exists."
    
    # Check if it's running
    if ! docker ps | grep -q lpe-postgres; then
        echo "🔄 Starting PostgreSQL container..."
        docker start lpe-postgres
        sleep 5
    else
        echo "✓ PostgreSQL container is already running."
    fi
else
    echo "📦 Creating PostgreSQL container..."
    docker-compose up -d
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 10
fi

# Wait for PostgreSQL to be fully ready
echo "🔍 Checking PostgreSQL connection..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker exec lpe-postgres pg_isready -U lpe_user > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready!"
        break
    fi
    echo "⏳ Waiting for PostgreSQL to be ready... (attempt $((attempt+1))/$max_attempts)"
    sleep 2
    attempt=$((attempt+1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ PostgreSQL failed to start properly."
    exit 1
fi

# Create the database if it doesn't exist
echo "🏗️ Creating database 'lamish_projection_engine' if it doesn't exist..."
docker exec lpe-postgres psql -U lpe_user -tc "SELECT 1 FROM pg_database WHERE datname = 'lamish_projection_engine'" | grep -q 1 || \
docker exec lpe-postgres psql -U lpe_user -c "CREATE DATABASE lamish_projection_engine"

# Create pgvector extension
echo "🔧 Creating pgvector extension..."
docker exec lpe-postgres psql -U lpe_user -d lamish_projection_engine -c "CREATE EXTENSION IF NOT EXISTS vector"

# Check the setup
echo ""
echo "📊 Database Status:"
echo "=================="
docker exec lpe-postgres psql -U lpe_user -d lamish_projection_engine -c "\l" | grep lamish_projection_engine
echo ""
echo "Extensions:"
docker exec lpe-postgres psql -U lpe_user -d lamish_projection_engine -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

echo ""
echo "✅ Database setup complete!"
echo ""
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: lamish_projection_engine"
echo "  User: lpe_user"
echo "  Password: lpe_password"